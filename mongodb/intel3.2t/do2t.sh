#!/bin/bash

pushd /opt/app/benchmark/mongodb/intel3.2t
sh split_loadrun-cases.sh;sh dointel2tlf8kb.sh;sh dovanda2t.sh
