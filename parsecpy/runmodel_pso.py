#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    Module to run a model of a parsec application.

    Its possible define the number of threads to execute a model
    on a fast way; The modelfunc to represent the application should be
    provided by user on a python module file. Its possible, also, provide a
    overhead function to integrate the model

    usage: parsecpy_runmodel_pso [-h] --config CONFIG -f PARSECPYFILEPATH
                             [-p PARTICLES] [-x MAXITERATIONS]
                             [-l LOWERVALUES] [-u UPPERVALUES]
                             [-n PROBLEMSIZES] [-o OVERHEAD] [-t THREADS]
                             [-r REPETITIONS] [-c CROSSVALIDATION]
                             [-v VERBOSITY]

    Script to run swarm modelling to predict aparsec application output

    optional arguments:
      -h, --help            show this help message and exit
      --config CONFIG       Filepath from Configuration file configurations
                            parameters
      -p PARSECPYFILEPATH, --parsecpyfilepath PARSECPYFILEPATH
                            Path from input data file from Parsec specificated
                            package.
      -q PARTICLES, --particles PARTICLES
                            Number of particles
      -x MAXITERATIONS, --maxiterations MAXITERATIONS
                            Number max of iterations
      -l LOWERVALUES, --lowervalues LOWERVALUES
                            List of minimum particles values used. Ex: -1,0,-2,0
      -u UPPERVALUES, --uppervalues UPPERVALUES
                            List of maximum particles values used. Ex: 5,2,1,10
      -f FREQUENCIES, --frequency FREQUENCIES
                            List of frequencies (KHz). Ex: 2000000, 2100000
      -n PROBLEMSIZES, --problemsizes PROBLEMSIZES
                            List of problem sizes to model used. Ex:
                            native_01,native_05,native_08
      -o OVERHEAD, --overhead OVERHEAD
                            If it consider the overhead
      -t THREADS, --threads THREADS
                            Number of Threads
      -r REPETITIONS, --repetitions REPETITIONS
                            Number of repetitions to algorithm execution
      -c CROSSVALIDATION, --crossvalidation CROSSVALIDATION
                            If run the cross validation of modelling
      -v VERBOSITY, --verbosity VERBOSITY
                            verbosity level. 0 = No verbose
    Example
        parsecpy_runmodel_pso -l -10,-10,-10,-10,-10 -u 10,10,10,10,10
            -f /var/myparsecsim.dat --config /var/myconfig.json -x 1000 -p 10
"""

import os
import sys
import json
import time
import argparse
from copy import deepcopy
from parsecpy import ParsecData
from parsecpy import Swarm
from parsecpy import argsparselist, argsparsefloatlist, argsparseintlist, \
    data_detach


def argsparsevalidation():
    """
    Validation of script arguments passed via console.

    :return: argparse object with validated arguments.
    """

    parser = argparse.ArgumentParser(description='Script to run swarm '
                                                 'modelling to predict a'
                                                 'parsec application output')
    parser.add_argument('--config', required=True,
                        help='Filepath from Configuration file '
                             'configurations parameters')
    parser.add_argument('-p', '--parsecpyfilepath',
                        help='Path from input data file from Parsec '
                             'specificated package.')
    parser.add_argument('-q', '--particles', type=int,
                        help='Number of particles')
    parser.add_argument('-x', '--maxiterations', type=int,
                        help='Number max of iterations')
    parser.add_argument('-l', '--lowervalues', type=argsparsefloatlist,
                        help='List of minimum particles values '
                             'used. Ex: -1,0,-2,0')
    parser.add_argument('-u', '--uppervalues',
                        help='List of maximum particles values used. '
                             'Ex: 5,2,1,10')
    parser.add_argument('-f', '--frequency', type=argsparseintlist,
                        help='List of frequencies (KHz). Ex: 2000000, 2100000')
    parser.add_argument('-n', '--problemsizes', type=argsparselist,
                        help='List of problem sizes to model used. '
                             'Ex: native_01,native_05,native_08')
    parser.add_argument('-o', '--overhead', type=bool,
                        help='If it consider the overhead')
    parser.add_argument('-t', '--threads', type=int,
                        help='Number of Threads')
    parser.add_argument('-r', '--repetitions', type=int,
                        help='Number of repetitions to algorithm execution')
    parser.add_argument('-c', '--crossvalidation', type=bool,
                        help='If run the cross validation of modelling')
    parser.add_argument('-v', '--verbosity', type=int,
                        help='verbosity level. 0 = No verbose')
    args = parser.parse_args()
    return args


def main():
    """
    Main function executed from console run.

    """

    print("\n***** Processing the Model *****")
    # adjust list of arguments to avoid negative number values error
    for i, arg in enumerate(sys.argv):
        if (arg[0] == '-') and arg[1].isdigit():
            sys.argv[i] = ' ' + arg

    args = argsparsevalidation()

    if args.config:
        if not os.path.isfile(args.config):
            print('Error: You should inform the correct config file path.')
            sys.exit()
        with open(args.config, 'r') as fconfig:
            config = json.load(fconfig)
        for i,v in vars(args).items():
            if v is not None:
                config[i] = v
    else:
        config = vars(args)

    if not os.path.isfile(config['modelfilepath']):
        print('Error: You should inform the correct module of '
              'objective function to model')
        sys.exit()

    if not os.path.isfile(config['parsecpyfilepath']):
        print('Error: You should inform the correct parsecpy measures file')
        sys.exit()

    lv = config['lowervalues']
    uv = config['uppervalues']

    parsec_exec = ParsecData(config['parsecpyfilepath'])
    y_measure = parsec_exec.speedups()
    input_sizes = []
    if 'size' in y_measure.dims:
        input_sizes = y_measure.attrs['input_sizes']
        input_ord = []
        if 'problemsizes' in config.keys():
                for i in config['problemsizes']:
                    if i not in input_sizes:
                        print('Error: Measures not has especified sizes')
                        sys.exit()
                    input_ord.append(input_sizes.index(i)+1)
                y_measure = y_measure.sel(size=sorted(input_ord))
                y_measure.attrs['input_sizes'] = sorted(config['problemsizes'])

    if 'frequency' in y_measure.dims:
        frequencies = y_measure.coords['frequency']
        if 'frequency' in config.keys():
                for i in config['frequency']:
                    if i not in frequencies:
                        print('Error: Measures not has especified frequencies')
                        sys.exit()
                y_measure = y_measure.sel(size=sorted(config['frequencies']))

    y_measure_detach = data_detach(y_measure)
    argsswarm = (config['overhead'], {'x': y_measure_detach['x'],
                                      'y': y_measure_detach['y'],
                                      'dims': y_measure.dims,
                                      'input_sizes': input_sizes})

    repetitions = range(config['repetitions'])
    err_min = 0
    computed_models = []
    best_model_idx = 0

    starttime = time.time()
    for i in repetitions:
        print('\nAlgorithm Execution: ', i+1)

        sw = Swarm(lv, uv, parsecpydatapath=config['parsecpyfilepath'],
                   modelcodepath=config['modelfilepath'],
                   size=config['particles'], w=config['w'], c1=config['c1'],
                   c2=config['c2'], maxiter=config['maxiterations'],
                   threads=config['threads'], verbosity=config['verbosity'],
                   args=argsswarm)
        model = sw.run()
        computed_models.append(model)
        if i == 0:
            err_min = model.error
            print('  Error: %.8f' % err_min)
        else:
            if model.error < err_min:
                best_model_idx = i
                print('  Error: %.8f -> %.8f ' % (err_min, model.error))
                err_min = model.error
        endtime = time.time()
        print('  Execution time = %.2f seconds' % (endtime - starttime))
        starttime = endtime

    print('\n\n***** Modelling Results! *****\n')
    print('Error: %.8f \nPercentual Error (Measured Mean): %.2f %%' %
          (computed_models[best_model_idx].error,
           computed_models[best_model_idx].errorrel))
    if config['verbosity'] > 0:
        print('Best Parameters: \n', computed_models[best_model_idx].params)
    if config['verbosity'] > 1:
        print('\nMeasured Speedup: \n', y_measure)
        print('\nModeled Speedup: \n', computed_models[best_model_idx].y_model)

    print('\n***** Modelling Done! *****\n')

    if config['crossvalidation']:
        print('\n\n***** Starting cross validation! *****\n')
        starttime = time.time()
        validation_model = deepcopy(computed_models[best_model_idx])
        scores = validation_model.validate(kfolds=10)
        print('\n  Cross Validation (K-fold, K=10) Metrics: ')
        if config['verbosity'] > 2:
            print('\n   Times: ')
            for key, value in scores['times'].items():
                print('     %s: %.8f' % (key, value.mean()))
                print('     ', value)
        print('\n   Scores: ')
        for key, value in scores['scores'].items():
            if config['verbosity'] > 1:
                print('     %s: %.8f' % (value['description'],
                                         value['value'].mean()))
                print('     ', value['value'])
            else:
                print('     %s: %.8f' % (value['description'],
                                         value['value'].mean()))
        endtime = time.time()
        print('  Execution time = %.2f seconds' % (endtime - starttime))
        computed_models[best_model_idx].validation = scores
        print('\n***** Cross Validation Done! *****\n')
    print('\n\n***** ALL DONE! *****\n')
    fn = computed_models[best_model_idx].savedata(parsec_exec.config, ' '.join(sys.argv))
    print('Model data saved on filename: %s' % fn)


if __name__ == '__main__':
    main()
