#!/bin/bash

NEXTFLOWDIR=/home/jch/Documents/09-fragfold/FragFold/nextflow #directory containing nextflow scripts
WORKDIR="/home/jch/Documents/data/fragfold_test/sample_test" #directory where results will be stored
NF_CFG=${NEXTFLOWDIR}/nextflow.config
PARAMS=${NEXTFLOWDIR}/params/ftsZ_monomeric_example.yaml
mkdir -p $WORKDIR
nextflow run ${NEXTFLOWDIR}/main.nf -w $WORKDIR -c $NF_CFG -params-file $PARAMS -with-dag dag.html -with-timeline -with-trace -with-report
# nextflow run ${NEXTFLOWDIR}/main.nf -w $WORKDIR -c $NF_CFG -params-file $PARAMS -resume -with-dag dag.html -with-timeline -with-trace -with-report
