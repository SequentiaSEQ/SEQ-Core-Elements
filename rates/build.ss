#!/usr/bin/env gxi
;;; -*- Gerbil -*-
(import
  :clan/building
  :std/sugar)

(def (files)
  [(all-gerbil-modules) ...
   [exe: "rates"]])

(init-build-environment!
  name: "rates"
  deps: '("clan")
  spec: files)
