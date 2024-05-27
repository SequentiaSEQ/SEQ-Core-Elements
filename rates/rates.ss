#!/usr/bin/env gxi
;; -*- Gerbil -*-
;;;;; Rates server

;; BEWARE: >>>> CONFIGURATION <<<<
;; copy the sample rates-assets-config.json and rates-services-config.json
;; from ./ to ~/.config/sequentia/ and edit rates-services-config.json to use your keys,
;; as gotten from:
;; https://www.coinapi.io/get-free-api-key?email=xxx
;; https://coinlayer.com/product (choose the free plan, still need a credit card)
;; https://coinmarketcap.com/api/pricing/ (choose the free plan)
;; https://site.financialmodelingprep.com/developer/docs/pricing (choose the basic plan)
;; https://polygon.io/dashboard/stocks

;; >>>> RUNNING IT <<<<
;; Build with
;;     ./build.ss
;; Run the server with
;;     ./rates.ss
;; or the compiled version with in
;;     ${GERBIL_PATH:-~/.gerbil}/bin/rates
;; Be sure to hide behind a firewall, with a SSL reverse proxy...
;; or configure the httpd as SSL (to be documented)
;; Then query it with
;;     curl -L http://localhost:29256/getfeeexchangerates
;; or feed it into sequentia with:
;;     elements-cli setfeeexchangerates $(curl -L http://localhost:29256/getfeeexchangerates)

(export #t)
;;; Imports

(import
  (group-in :std format iter sort sugar)
  (group-in :std/cli getopt multicall)
  (group-in :std/misc hash path number)
  (group-in :std/net httpd request uri)
  (only-in :std/net/address inet-address->string)
  (group-in :std/srfi |1|)
  (group-in :std/text json)
  (only-in :std/markup/xml write-xml)
  (group-in :clan config files json timestamp))

(import ;; for development and debugging
  (group-in :std/debug DBG)
  (group-in :std/misc ports repr)
  (group-in :clan debug))


;;; General utility functions, to move somewhere else

;; Compute the median of a list of reals
;; Real <- (Listof Real)
(def (median l (default 0))
  (def s (sort l <))
  (def n (length l))
  (def i (half (1- n)))
  (def j (half n))
  (cond
   ((zero? n) default)
   ((= i j) (list-ref s i))
   (else (* .5 (+ (list-ref s i) (list-ref s j))))))

;; Access successive subnodes in a JSON object
(defrules hash-ref* ()
  ((h x) x)
  ((h x y . z) (h (hash-ref x y) . z)))

(def (pj x) (pretty-json x (current-output-port) lisp-style?: #t))

;; List to hash-table given
;; HashTable <- List
(def (list->hash-table/by-symbol lst (field "symbol"))
  (list->hash-table (map (lambda (x) (cons (hash-ref x field) x)) lst)))

;; Access a quote of given symbol from a list
;; HashTable <- (Listof HashTable) (Or String Fixnum)
(def (symbol-select data selector (field "symbol"))
  (cond
   ((string? selector) (find (lambda (x) (equal? (hash-ref x field) selector)) data))
   ((fixnum? selector) (list-ref data selector))
   (else (error "bad selector" selector))))

;; JSON <- String
(def (read-json-config file)
  (try (read-file-json file)
       (catch (_)
         (error "Failed to read and validate JSON config file (use jq to debug it?)" file))))

;;; A registry of named oracles and their access methods

;; (Table (List Function Function) <- String)
(def price-oracles (hash))

;; <- String Function Function
(def (register-price-oracle name get-quote get-rate)
  (hash-put! price-oracles name [get-quote get-rate]))

;; Get JSON from a HTTP GET
(def (http-get/json url . rest)
  (bytes->json-object
   (request-content
    (apply http-get url rest))))


;;; Configuration

;; (Parameter (Table HashTable <- String))
(def *rates-services-config*
  (make-parameter (hash)))

;; (Parameter (Table HashTable <- String))
(def *rates-assets-config*
  (make-parameter (hash)))

;; JSON <- JSON
(def (validate-services-config j)
  j)

;; JSON <- JSON
(def (validate-assets-config j)
  j)

;; <-
(def (read-rates-config)
  (*rates-services-config*
   (validate-services-config
    (read-json-config (xdg-config-home "sequentia/rates-services-config.json"))))
  (*rates-assets-config*
   (validate-assets-config
    (read-json-config (xdg-config-home "sequentia/rates-assets-config.json")))))


;;; Cached prices from oracles

;; For each oracle, the timestamp of last query attempt, timestamp of data, data (#f if none)
;; (Table (List TAI TAI JSON) <- String)
(def oracle-prices (hash))

;; String <-
(def (oracle-prices-cache-path)
  (xdg-cache-home "sequentia/oracle-prices.json"))

;; <-
(def (load-oracle-prices-cache)
  (set! oracle-prices
    (try
     (read-file-json (oracle-prices-cache-path))
     (catch (_)
       (eprintf "Price cache at ~a not present or invalid. Resetting cache state.\n"
                (oracle-prices-cache-path))
       (hash)))))

;; <-
(def (save-oracle-prices-cache)
  (create-directory* (xdg-cache-home "sequentia"))
  (clobber-file (oracle-prices-cache-path)
                (cut write-json oracle-prices <>)))

;; TODO: save pristine data as obtained from source, just compressed, in a sqlite database.

;;; Initialize environment for rates
(def (rates-environment)
  (read-json-key-as-symbol? #f)
  (write-json-sort-keys? #t)
  (read-rates-config)
  (load-oracle-prices-cache))

;;; Getting rates from lazily-updated cache of oracles

;; Given an oracle, return a list of the timestamp of last query attempt,
;; timestamp of data, and raw data as JSON object (#f if none)
;; (List TAI TAI JSON) <- String
(def (get-oracle-data oracle services-config: (services-config (*rates-services-config*)))
  (let/cc k
    (def (return x)
      (unless (equal? x (hash-get oracle-prices oracle))
        (hash-put! oracle-prices oracle x)
        (save-oracle-prices-cache))
      (k x))
    (def config (hash-get services-config oracle))
    (def refractory-period (if config (hash-ref config "refractory_period") +inf.0))
    (def (refresh)
      (match (hash-ref price-oracles oracle)
        ([get-quote _]
         (let* ((new-quote (get-quote config))
                (stamp (current-tai-timestamp))
                (result [stamp stamp new-quote]))
           (return result)))))
    (def (errlog e)
      (display-exception e (current-error-port))
      e)
    (def previous (hash-get oracle-prices oracle))
    (match previous
      ([attempt-tai data-tai quote-data]
       (when (and attempt-tai
                  (< (current-tai-timestamp)
                     (+ attempt-tai (* refractory-period one-second))))
         (return previous))
       (try
        (refresh)
        (catch (e)
          (eprintf "Failed to refresh price oracle ~a -- returning old value from ~a\n"
                   oracle (string<-tai-timestamp data-tai))
          (errlog e)
          (return [(current-tai-timestamp) data-tai quote-data]))))
      (_
       (try
        (refresh)
        (catch (e)
          (eprintf "Failed to query price oracle ~a -- returning false\n"
                   oracle)
          (errlog e)
          (return [#f #f #f])))))))

;; Given an oracle and an oracle-dependent path to extract data from the raw oracle,
;; return the rate corresponding to that path.
;; Real <- String Any services-config: ?JSON
(def (get-rate/oracle-path
      oracle path
      services-config: (services-config (*rates-services-config*)))
  (let (data (void))
    (try
     (set! data (third (get-oracle-data oracle services-config: services-config)))
     (match (hash-ref price-oracles oracle)
       ([_ get-rate]
        (get-rate data path)))
     (catch (e)
       (eprintf "Failed to extract from oracle ~a price for path ~a, data ~a\n"
                oracle (json-object->string path) (json-object->string data))
       #f))))

;; Given assets-config and services-config, and using the cache,
;; return a table that to each currency code (string) associates a table from service name (string)
;; to conversion rate (Real) from the currency to RFU (aka USD).
;; (Table (Table Real <- String) <- String) <- assets-config: ?JSON services-config: ?JSON
(def (get-rates
      assets-config: (assets-config (*rates-assets-config*))
      services-config: (services-config (*rates-services-config*)))
  (hash-value-map
   assets-config
   (lambda (asset)
     (hash-key-value-map
      (lambda (oracle path)
        (cons oracle (get-rate/oracle-path oracle path services-config: services-config)))
      (hash-ref asset "oracles")))))

;; Get the median rate among those available in a table, or #f if no rates are available.
;; Real <- (Table Real <- String)
(def (median<-rates rates)
  (median (filter identity (hash-values rates)) #f))

;; Get the median rates for the configured currencies
;; (Table Real <- String) <- assets-config: ?JSON services-config: ?JSON
(def (get-median-rates
      assets-config: (assets-config (*rates-assets-config*))
      services-config: (services-config (*rates-services-config*)))
  (hash-value-map
   (get-rates assets-config: assets-config
              services-config: services-config)
   median<-rates))

(def (normalize-rate x)
  (integer-part (round x)))

;; COIN = 1e8 (as integer).
;; We assume 1 RFU = COIN atoms of RFU just like 1 BTC = COIN satoshi
(def COIN-decimals 8)
(def COIN (expt 10 COIN-decimals))

(def (get-fee-exchange-rates
      assets-config: (assets-config (*rates-assets-config*))
      services-config: (services-config (*rates-services-config*)))
  (def rates (get-median-rates assets-config: assets-config
                               services-config: services-config))
  (def reference-asset (hash-ref assets-config "RFU" (hash)))
  (def reference-decimals (hash-ref reference-asset "decimals" COIN-decimals))
  (def reference-fudge-factor (hash-ref reference-asset "fudge_factor" 1))
  (def h (hash))
  (for (((values asset config) (in-hash assets-config)))
    (alet ((rate (hash-get rates asset))
           (nAsset (hash-get config "nAsset")))
      (hash-put! h nAsset
                 (normalize-rate
                  (/ (* rate
                        (hash-ref config "fudge_factor" 1)
                        (expt 10 (- reference-decimals
                                    (hash-ref config "decimals" COIN-decimals))))
                     reference-fudge-factor)))))
  h)

;;; The access methods

;; Macro to define a price oracle.
;; Usage: (defprice-oracle name get-quote-method get-rate-method)
;;
;; Name is a symbol for the name of the oracle.
;; An entry in the price-oracles hash-table will be register under the symbol name (string).
;; This entry will point to the defined get-FOO-quote and get-FOO-rate functions below,
;; where functions are defined with FOO replaced by the provided name.
;;
;; A new function get-FOO-quote will be defined based on the get-quote-method argument;
;; this get-quote-method argument must be of the form ((config) body1 ...) where
;; config is the name of a services-config variable, and body1 the body of the function;
;; the function will be defined with config being an optional argument that has a suitable
;; default extracted from the current *rates-services-config*.
;;
;; A new function get-FOO-rate will be defined based on the get-rate-method argument;
;; this get-rate-method argument must be of the form ((quote-json path) body2 ...) where
;; quote-json is a variable to be bound to the JSON data provided by the oracle, and
;; path is a variable to be bound to some oracle-dependent data to select a rate from that JSON data.
;; The function will be defined with these two variables as mandatory positional variables.
;;
;; See examples below.
(defrule (defprice-oracle name ((config) body1 ...) ((quote-json path) body2 ...))
  (with-id defprice-oracle ((get-quote 'get- #'name '-quote)
                            (get-rate 'get- #'name '-rate))
    (begin
      (def (get-quote (config (hash-ref (*rates-services-config*) (as-string 'name)))) body1 ...)
      (def (get-rate quote-json path) body2 ...)
      (register-price-oracle (as-string 'name) get-quote get-rate))))

;; Constant (for the Reference Fee Unit and any multiples of it)
;; The selector is the constant rate that you return.
(defprice-oracle constant
  ((config)
   #t)
  ((_quote-json selector)
   selector))

;; Blockchain.info (for Bitcoin price only)
;; https://www.blockchain.com/explorer/api/exchange_rates_api
;; https://blockchain.info/ticker
(defprice-oracle blockchain.info
  ((config)
   (bytes->json-object
    (request-content
     (http-get "https://blockchain.info/ticker"))))
  ((quote-json selector)
   (unless (equal? selector "BTC")
     (error "bad selector" selector))
   (hash-ref* quote-json "USD" "last")))

;; CEX.io
;; https://cex.io/rest-api#ticker
(defprice-oracle cex.io
  ((config)
   (bytes->json-object
    (request-content
     (http-get "https://cex.io/api/tickers/USD"))))
  ((quote-json selector)
   (string->number
    (hash-ref (symbol-select (hash-ref quote-json "data") selector "pair") "last"))))

;; Coinapi.io
;; https://docs.coinapi.io/
(defprice-oracle coinapi.io
  ((config)
   (let ((key (hash-ref config "key")))
     (http-get/json "https://rest.coinapi.io/v1/exchangerate/USD?invert=true"
                    headers: [["X-CoinAPI-Key" . key]])))
  ((quote-json selector)
   (hash-ref (symbol-select (hash-ref quote-json "rates") selector "asset_id_quote") "rate")))


;; Coinlayer.com
;; https://coinlayer.com/documentation
;; Free API key has only 100 queries per month, so set refractory period to 28800 (8 hours)
;; Also, free API can only use http, not https. There is no test server.
;; See how many queries you have left at: https://coinlayer.com/dashboard
(defprice-oracle coinlayer.com
  ((config)
   (let ((protocol (hash-ref config "protocol"))
         (key (hash-ref config "key")))
     (http-get/json (query-string (as-string protocol "://api.coinlayer.com/live")
                                  access_key: key))))
  ((quote-json selector)
   (hash-ref* quote-json "rates" selector)))

;; Coinmarketcap.com
;; https://coinmarketcap.com/api/documentation/v1/#section/Quick-Start-Guide
;; NB: Free has 10K calls per month, so safe once every 2 hours,
;; or once a minute for about 2h45. https://pro.coinmarketcap.com/api/pricing
;; The $30/mo plan has 110K calls per month, enough for twice a minute
;; Test server serves garbage, albeit in the right format.
(defprice-oracle coinmarketcap.com
  ((config)
   (let ((key (hash-ref config "key")))
     (http-get/json (query-string "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
                                  start: 1 limit: 5000 convert: 'USD)
                    headers: [["X-CMC_PRO_API_KEY" . key]
                              ["Accept" . "application/json"]])))
  ((quote-json selector)
   (hash-ref* (symbol-select (hash-ref quote-json "data") selector) "quote" "USD" "price")))

;; Financialmodelingprep.com
;; https://site.financialmodelingprep.com/developer/docs/bitcoin-price-free-api
;; free is 250 calls/day, with 2 things, every 6 minutes
(defprice-oracle financialmodelingprep.com
  ((config)
   (let* ((key (hash-ref config "key"))
          (pairs (hash-ref config "asset_pairs"))
          (url (as-string "https://financialmodelingprep.com/api/v3/quote/" pairs)))
     (list->hash-table/by-symbol
      (http-get/json (query-string url apikey: key)))))
  ((quote-json selector)
   (hash-ref* quote-json selector "price")))

;; Polygon.io
;; https://polygon.io/docs/stocks/get_v2_last_nbbo__stocksticker
;; Access requires $80/mo subscription for up-to-date data... not for now
;; Free access offers unlimited access to.. the closing price the previous day.
(defprice-oracle polygon.io
  ((config)
   (let ((key (hash-ref config "key"))
         (tickers (hash-ref config "tickers")))
     (list->hash-table
      (map (lambda (ticker)
             (cons ticker
                   (http-get/json (query-string ;; only previous close fro
                                   (as-string "https://api.polygon.io/v2/aggs/ticker/" ticker "/prev")
                                   apiKey: key))))
           tickers))))
  ((quote-json selector)
   ;; This is very imprecise, only close from last day
   (hash-ref (symbol-select (hash-ref* quote-json selector "results") selector "T") "c")))

;; TODO: add more data sources?
;; https://medium.com/coinmonks/free-stock-apis-de8f13619911
;; https://www.alphavantage.co/documentation/
;; https://finnhub.io/
;; https://snowtrace.io/documentation#api-plans

;;; TODO: Connecting to a sequentia node


;; /rates -- handler for the rates page
(def rates-mutex (make-mutex "rates"))
(def (rates-handler req res)
  (with-lock
   rates-mutex
   (cut http-response-write
        res 200 '(("Content-Type" . "application/json-rpc"))
        (json-object->string (get-rates)))))

;; /getfeeexchangerates -- handler for the rates page
(def (getfeeexchangerates-handler req res)
  (with-lock
   rates-mutex
   (cut http-response-write
        res 200 '(("Content-Type" . "application/json-rpc"))
        (json-object->string (get-fee-exchange-rates)))))

;; / -- handler for the main page
(def (root-handler req res)
  (http-response-write
   res 200 '(("Content-Type" . "text/html"))
   (with-output-to-string []
     (cut write-xml
          `(html
            (head
             (meta (@ (http-equiv "Content-Type") (content "text/html; charset=utf-8")))
             (title "Sequentia Rates Server")
             (body
              (h1 "Hello, " ,(inet-address->string (http-request-client req)))
              (p "Welcome to this "
                 (a (@ (href "https://sequentia.io")) "Sequentia")
                 " rates server. "
                 "Please use "
                 (a (@ (href "/rates")) "our JSON-RPC interface") "."))))))))

;; default -- 404
(def (default-handler req res)
  (http-response-write res 404 '(("Content-Type" . "text/plain")) "Page not found."))

(def handlers
  [["/" root-handler]
   ["/rates" rates-handler]
   ["/getfeeexchangerates" getfeeexchangerates-handler]])

;; 29256 comes from the last bytes of echo -n 'sequentia rates server' | sha256sum
(define-entry-point (server address: (address "0.0.0.0:29256"))
  (help: "Start a server"
   getopt: [(option 'address "-a" "--address"
            help: "Address on which to start a server"
            default: "0.0.0.0:29256")])
  (rates-environment)
  (displayln "Current rates are:")
  (pj (get-rates))
  (displayln "See price cache at: " (oracle-prices-cache-path))
  ;; TODO: have a verbose flag to control that?
  (displayln "Starting an HTTP daemon listening on " address)
  ;; Start the HTTP daemon
  (def httpd (start-http-server! address mux: (make-default-http-mux default-handler)))
  ;; Register the handlers
  (for-each (cut apply http-register-handler httpd <>) handlers)
  ;; Wait for it to end
  (thread-join! httpd))

(define-entry-point (getrates)
  (help: "Pretty-print rates"
   getopt: [])
  (rates-environment)
  (pj (get-rates)))

(define-entry-point (getfeeexchangerates)
  (help: "Pretty-print getfeeexchangerates data"
   getopt: [])
  (rates-environment)
  (pj (get-fee-exchange-rates)))

(define-entry-point (selfcheck)
  (help: "Entry-Point to debug the binary"
   getopt: [])
  (displayln "foo")
  (clobber-file "/tmp/foo"
                (lambda (p)
                  (display "barbaz\n" p)
                  (write (current-output-port) p)
                  )))

(set-default-entry-point! 'server)
;(dump-stack-trace? #f)
(define-multicall-main)
