# -*- coding: utf-8 -*-
#  CCP in Tomographic Imaging (CCPi) Core Imaging Library (CIL).

#   Copyright 2017 UKRI-STFC
#   Copyright 2017 University of Manchester

#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
from __future__ import division

import unittest
import numpy
import numpy as np
from cil.framework import DataContainer
from cil.framework import ImageData
from cil.framework import AcquisitionData
from cil.framework import ImageGeometry
from cil.framework import AcquisitionGeometry
from cil.framework import BlockDataContainer

from cil.optimisation.operators import IdentityOperator
from cil.optimisation.operators import GradientOperator, BlockOperator, FiniteDifferenceOperator

from cil.optimisation.functions import LeastSquares, ZeroFunction, \
   L2NormSquared, OperatorCompositionFunction
from cil.optimisation.functions import MixedL21Norm, BlockFunction, L1Norm, KullbackLeibler                     
from cil.optimisation.functions import IndicatorBox

from cil.optimisation.algorithms import Algorithm
from cil.optimisation.algorithms import GD
from cil.optimisation.algorithms import CGLS
from cil.optimisation.algorithms import SIRT
from cil.optimisation.algorithms import FISTA
from cil.optimisation.algorithms import SPDHG
from cil.optimisation.algorithms import PDHG
from cil.optimisation.algorithms import LADMM

from cil.utilities import dataexample
from cil.utilities import noise as applynoise
import os, sys, time


# Fast Gradient Projection algorithm for Total Variation(TV)
from cil.optimisation.functions import TotalVariation

try:
    from cil.plugins.astra.operators import AstraProjectorSimple
    has_astra = True    
except ImportError as ie:
    # skip test
    has_astra = False

class TestAlgorithms(unittest.TestCase):
    def setUp(self):
        #wget.download('https://github.com/DiamondLightSource/Savu/raw/master/test_data/data/24737_fd.nxs')
        #self.filename = '24737_fd.nxs'
        # we use Identity as the operator and solve the simple least squares 
        # problem for a random-valued ImageData or AcquisitionData b?  
        # Then we know the minimiser is b itself
        
        # || I x -b ||^2
        
        # create an ImageGeometry
        ig = ImageGeometry(12,13,14)
        pass

    def tearDown(self):
        #os.remove(self.filename)
        pass
    
    def test_GD(self):
        print ("Test GD")
        ig = ImageGeometry(12,13,14)
        initial = ig.allocate()
        # b = initial.copy()
        # fill with random numbers
        # b.fill(numpy.random.random(initial.shape))
        b = ig.allocate('random')
        identity = IdentityOperator(ig)
        
        norm2sq = LeastSquares(identity, b)
        rate = norm2sq.L / 3.
        
        alg = GD(initial=initial, 
                              objective_function=norm2sq, 
                              rate=rate, atol=1e-9, rtol=1e-6)
        alg.max_iteration = 1000
        alg.run()
        self.assertNumpyArrayAlmostEqual(alg.x.as_array(), b.as_array())
        alg = GD(initial=initial, 
                              objective_function=norm2sq, 
                              rate=rate, max_iteration=20,
                              update_objective_interval=2,
                              atol=1e-9, rtol=1e-6)
        alg.max_iteration = 20
        self.assertTrue(alg.max_iteration == 20)
        self.assertTrue(alg.update_objective_interval==2)
        alg.run(20, verbose=True)
        self.assertNumpyArrayAlmostEqual(alg.x.as_array(), b.as_array())
    def test_GDArmijo(self):
        print ("Test GD")
        ig = ImageGeometry(12,13,14)
        initial = ig.allocate()
        # b = initial.copy()
        # fill with random numbers
        # b.fill(numpy.random.random(initial.shape))
        b = ig.allocate('random')
        identity = IdentityOperator(ig)
        
        norm2sq = LeastSquares(identity, b)
        rate = None
        
        alg = GD(initial=initial, 
                              objective_function=norm2sq, rate=rate)
        alg.max_iteration = 100
        alg.run()
        self.assertNumpyArrayAlmostEqual(alg.x.as_array(), b.as_array())
        alg = GD(initial=initial, 
                              objective_function=norm2sq, 
                              max_iteration=20,
                              update_objective_interval=2)
        #alg.max_iteration = 20
        self.assertTrue(alg.max_iteration == 20)
        self.assertTrue(alg.update_objective_interval==2)
        alg.run(20, verbose=True)
        self.assertNumpyArrayAlmostEqual(alg.x.as_array(), b.as_array())
    def test_GDArmijo2(self):
        from cil.optimisation.functions import Rosenbrock
        from cil.framework import VectorData, VectorGeometry

        f = Rosenbrock (alpha = 1., beta=100.)
        vg = VectorGeometry(2)
        x = vg.allocate('random_int', seed=2)
        # x = vg.allocate('random', seed=1) 
        x.fill(numpy.asarray([10.,-3.]))
        
        max_iter = 10000
        update_interval = 1000

        alg = GD(x, f, max_iteration=max_iter, update_objective_interval=update_interval, alpha=1e6)
        
        alg.run()
        
        print (alg.get_output().as_array(), alg.step_size, alg.kmax, alg.k)

        # this with 10k iterations
        numpy.testing.assert_array_almost_equal(alg.get_output().as_array(), [0.13463363, 0.01604593], decimal = 6)
        # this with 1m iterations
        # numpy.testing.assert_array_almost_equal(alg.get_output().as_array(), [1,1], decimal = 1)
        # numpy.testing.assert_array_almost_equal(alg.get_output().as_array(), [0.982744, 0.965725], decimal = 6)

    def test_CGLS(self):
        print ("Test CGLS")
        #ig = ImageGeometry(124,153,154)
        ig = ImageGeometry(10,2)
        numpy.random.seed(2)
        initial = ig.allocate(0.)
        b = ig.allocate('random')
        # b = initial.copy()
        # fill with random numbers
        # b.fill(numpy.random.random(initial.shape))
        # b = ig.allocate()
        # bdata = numpy.reshape(numpy.asarray([i for i in range(20)]), (2,10))
        # b.fill(bdata)
        identity = IdentityOperator(ig)
        
        alg = CGLS(initial=initial, operator=identity, data=b)
        alg.max_iteration = 200
        alg.run(20, verbose=True)
        self.assertNumpyArrayAlmostEqual(alg.x.as_array(), b.as_array())

        alg = CGLS(initial=initial, operator=identity, data=b, max_iteration=200, update_objective_interval=2)
        self.assertTrue(alg.max_iteration == 200)
        self.assertTrue(alg.update_objective_interval==2)
        alg.run(20, verbose=True)
        self.assertNumpyArrayAlmostEqual(alg.x.as_array(), b.as_array())
    
        
    def test_FISTA(self):
        print ("Test FISTA")
        ig = ImageGeometry(127,139,149)
        initial = ig.allocate()
        b = initial.copy()
        # fill with random numbers
        b.fill(numpy.random.random(initial.shape))
        initial = ig.allocate(ImageGeometry.RANDOM)
        identity = IdentityOperator(ig)
        
	#### it seems FISTA does not work with Nowm2Sq
        # norm2sq = Norm2Sq(identity, b)
        # norm2sq.L = 2 * norm2sq.c * identity.norm()**2
        norm2sq = OperatorCompositionFunction(L2NormSquared(b=b), identity)
        opt = {'tol': 1e-4, 'memopt':False}
        print ("initial objective", norm2sq(initial))
        alg = FISTA(initial=initial, f=norm2sq, g=ZeroFunction())
        alg.max_iteration = 2
        alg.run(20, verbose=True)
        self.assertNumpyArrayAlmostEqual(alg.x.as_array(), b.as_array())

        alg = FISTA(initial=initial, f=norm2sq, g=ZeroFunction(), max_iteration=2, update_objective_interval=2)
        
        self.assertTrue(alg.max_iteration == 2)
        self.assertTrue(alg.update_objective_interval==2)

        alg.run(20, verbose=True)
        self.assertNumpyArrayAlmostEqual(alg.x.as_array(), b.as_array())

               
    def test_FISTA_Norm2Sq(self):
        print ("Test FISTA Norm2Sq")
        ig = ImageGeometry(127,139,149)
        b = ig.allocate(ImageGeometry.RANDOM)
        # fill with random numbers
        initial = ig.allocate(ImageGeometry.RANDOM)
        identity = IdentityOperator(ig)
        
	    #### it seems FISTA does not work with Nowm2Sq
        norm2sq = LeastSquares(identity, b)
        #norm2sq.L = 2 * norm2sq.c * identity.norm()**2
        #norm2sq = OperatorCompositionFunction(L2NormSquared(b=b), identity)
        opt = {'tol': 1e-4, 'memopt':False}
        print ("initial objective", norm2sq(initial))
        alg = FISTA(initial=initial, f=norm2sq, g=ZeroFunction())
        alg.max_iteration = 2
        alg.run(20, verbose=True)
        self.assertNumpyArrayAlmostEqual(alg.x.as_array(), b.as_array())

        alg = FISTA(initial=initial, f=norm2sq, g=ZeroFunction(), max_iteration=2, update_objective_interval=3)
        self.assertTrue(alg.max_iteration == 2)
        self.assertTrue(alg.update_objective_interval== 3)

        alg.run(20, verbose=True)
        self.assertNumpyArrayAlmostEqual(alg.x.as_array(), b.as_array())

    def test_FISTA_catch_Lipschitz(self):
        print ("Test FISTA catch Lipschitz")
        ig = ImageGeometry(127,139,149)
        initial = ImageData(geometry=ig)
        initial = ig.allocate()
        b = initial.copy()
        # fill with random numbers  
        b.fill(numpy.random.random(initial.shape))
        initial = ig.allocate(ImageGeometry.RANDOM)
        identity = IdentityOperator(ig)
        
	    #### it seems FISTA does not work with Nowm2Sq
        norm2sq = LeastSquares(identity, b)
        print ('Lipschitz', norm2sq.L)
        # norm2sq.L = None
        #norm2sq.L = 2 * norm2sq.c * identity.norm()**2
        #norm2sq = OperatorCompositionFunction(L2NormSquared(b=b), identity)
        opt = {'tol': 1e-4, 'memopt':False}
        print ("initial objective", norm2sq(initial))
        try:
            alg = FISTA(initial=initial, f=L1Norm(), g=ZeroFunction())
            self.assertTrue(False)
        except ValueError as ve:
            print (ve)
            self.assertTrue(True)
    def test_PDHG_Denoising(self):
        print ("PDHG Denoising with 3 noises")
        # adapted from demo PDHG_TV_Color_Denoising.py in CIL-Demos repository
        
        data = dataexample.PEPPERS.get(size=(256,256))
        ig = data.geometry
        ag = ig

        which_noise = 0
        # Create noisy data. 
        noises = ['gaussian', 'poisson', 's&p']
        dnoise = noises[which_noise]
        
        def setup(data, dnoise):
            if dnoise == 's&p':
                n1 = applynoise.saltnpepper(data, salt_vs_pepper = 0.9, amount=0.2, seed=10)
            elif dnoise == 'poisson':
                scale = 5
                n1 = applynoise.poisson( data.as_array()/scale, seed = 10)*scale
            elif dnoise == 'gaussian':
                n1 = applynoise.gaussian(data.as_array(), seed = 10)
            else:
                raise ValueError('Unsupported Noise ', noise)
            noisy_data = ig.allocate()
            noisy_data.fill(n1)
        
            # Regularisation Parameter depending on the noise distribution
            if dnoise == 's&p':
                alpha = 0.8
            elif dnoise == 'poisson':
                alpha = 1
            elif dnoise == 'gaussian':
                alpha = .3
                # fidelity
            if dnoise == 's&p':
                g = L1Norm(b=noisy_data)
            elif dnoise == 'poisson':
                g = KullbackLeibler(b=noisy_data)
            elif dnoise == 'gaussian':
                g = 0.5 * L2NormSquared(b=noisy_data)
            return noisy_data, alpha, g

        noisy_data, alpha, g = setup(data, dnoise)
        operator = GradientOperator(ig, correlation=GradientOperator.CORRELATION_SPACE)

        f1 =  alpha * MixedL21Norm()

        
                    
        # Compute operator Norm
        normK = operator.norm()

        # Primal & dual stepsizes
        sigma = 1
        tau = 1/(sigma*normK**2)

        # Setup and run the PDHG algorithm
        pdhg1 = PDHG(f=f1,g=g,operator=operator, tau=tau, sigma=sigma)
        pdhg1.max_iteration = 2000
        pdhg1.update_objective_interval = 200
        pdhg1.run(1000, very_verbose=True)

        rmse = (pdhg1.get_output() - data).norm() / data.as_array().size
        print ("RMSE", rmse)
        self.assertLess(rmse, 2e-4)

        which_noise = 1
        noise = noises[which_noise]
        noisy_data, alpha, g = setup(data, noise)
        operator = GradientOperator(ig, correlation=GradientOperator.CORRELATION_SPACE)

        f1 =  alpha * MixedL21Norm()

        
                    
        # Compute operator Norm
        normK = operator.norm()

        # Primal & dual stepsizes
        sigma = 1
        tau = 1/(sigma*normK**2)

        # Setup and run the PDHG algorithm
        pdhg1 = PDHG(f=f1,g=g,operator=operator, tau=tau, sigma=sigma, 
                     max_iteration=2000, update_objective_interval=200)
        
        pdhg1.run(1000)

        rmse = (pdhg1.get_output() - data).norm() / data.as_array().size
        print ("RMSE", rmse)
        self.assertLess(rmse, 2e-4)
        
        
        which_noise = 2
        noise = noises[which_noise]
        noisy_data, alpha, g = setup(data, noise)
        operator = GradientOperator(ig, correlation=GradientOperator.CORRELATION_SPACE)

        f1 =  alpha * MixedL21Norm()
   
        # Compute operator Norm
        normK = operator.norm()

        # Primal & dual stepsizes
        sigma = 1
        tau = 1/(sigma*normK**2)

        # Setup and run the PDHG algorithm
        pdhg1 = PDHG(f=f1,g=g,operator=operator, tau=tau, sigma=sigma)
        pdhg1.max_iteration = 2000
        pdhg1.update_objective_interval = 200
        pdhg1.run(1000)

        rmse = (pdhg1.get_output() - data).norm() / data.as_array().size
        print ("RMSE", rmse)
        self.assertLess(rmse, 2e-4)

    def test_FISTA_Denoising(self):
        print ("FISTA Denoising Poisson Noise Tikhonov")
        # adapted from demo FISTA_Tikhonov_Poisson_Denoising.py in CIL-Demos repository
        data = dataexample.SHAPES.get()
        ig = data.geometry
        ag = ig
        N=300
        # Create Noisy data with Poisson noise
        scale = 5
        noisy_data = applynoise.poisson(data/scale,seed=10) * scale

        # Regularisation Parameter
        alpha = 10

        # Setup and run the FISTA algorithm
        operator = GradientOperator(ig)
        fid = KullbackLeibler(b=noisy_data)
        reg = OperatorCompositionFunction(alpha * L2NormSquared(), operator)

        initial = ig.allocate()
        fista = FISTA(initial=initial , f=reg, g=fid)
        fista.max_iteration = 3000
        fista.update_objective_interval = 500
        fista.run(verbose=True)
        rmse = (fista.get_output() - data).norm() / data.as_array().size
        print ("RMSE", rmse)
        self.assertLess(rmse, 4.2e-4)

    def assertNumpyArrayEqual(self, first, second):
        res = True
        try:
            numpy.testing.assert_array_equal(first, second)
        except AssertionError as err:
            res = False
            print(err)
        self.assertTrue(res)

    def assertNumpyArrayAlmostEqual(self, first, second, decimal=6):
        res = True
        try:
            numpy.testing.assert_array_almost_equal(first, second, decimal)
        except AssertionError as err:
            res = False
            print(err)
        self.assertTrue(res)

    def test_exception_initial_SIRT(self):
        print ("Test CGLS")
        ig = ImageGeometry(10,2)
        numpy.random.seed(2)
        initial = ig.allocate(0.)
        b = ig.allocate('random')
        identity = IdentityOperator(ig)
        
        try:
            alg = SIRT(initial=initial, operator=identity, data=b, x_init=initial)
            assert False
        except ValueError as ve:
            assert True
    def test_exception_initial_CGLS(self):
        print ("Test CGLS")
        ig = ImageGeometry(10,2)
        numpy.random.seed(2)
        initial = ig.allocate(0.)
        b = ig.allocate('random')
        identity = IdentityOperator(ig)
        
        try:
            alg = SIRT(initial=initial, operator=identity, data=b, x_init=initial)
            assert False
        except ValueError as ve:
            assert True
    def test_exception_initial_FISTA(self):
        print ("Test FISTA")
        ig = ImageGeometry(127,139,149)
        initial = ig.allocate()
        b = initial.copy()
        # fill with random numbers
        b.fill(numpy.random.random(initial.shape))
        initial = ig.allocate(ImageGeometry.RANDOM)
        identity = IdentityOperator(ig)
        
        norm2sq = OperatorCompositionFunction(L2NormSquared(b=b), identity)
        opt = {'tol': 1e-4, 'memopt':False}
        print ("initial objective", norm2sq(initial))
        try:
            alg = FISTA(initial=initial, f=norm2sq, g=ZeroFunction(), x_init=initial)
            assert False
        except ValueError as ve:
            assert True
    def test_exception_initial_GD(self):
        print ("Test FISTA")
        ig = ImageGeometry(127,139,149)
        initial = ig.allocate()
        b = initial.copy()
        # fill with random numbers
        b.fill(numpy.random.random(initial.shape))
        initial = ig.allocate(ImageGeometry.RANDOM)
        identity = IdentityOperator(ig)
        
        norm2sq = OperatorCompositionFunction(L2NormSquared(b=b), identity)
        opt = {'tol': 1e-4, 'memopt':False}
        print ("initial objective", norm2sq(initial))
        try:
            alg = GD(initial=initial, objective_function=norm2sq, x_init=initial)
            assert False
        except ValueError as ve:
            assert True
    def test_exception_initial_LADMM(self):
        ig = ImageGeometry(10,10)
        # K = Identity(ig)
        # b = ig.allocate(0)
        # f = LeastSquares(K, b)
        # g = IndicatorBox(lower=0)
        initial = ig.allocate(1)
        try:
            algo = LADMM(initial = initial, x_init=initial)
            assert False
        except ValueError as ve:
            assert True
    def test_exception_initial_PDHG(self):
        initial = 1
        try:
            algo = PDHG(initial = initial, x_init=initial)
            assert False
        except ValueError as ve:
            assert True
    def test_exception_initial_SPDHG(self):
        initial = 1
        try:
            algo = SPDHG(initial = initial, x_init=initial)
            assert False
        except ValueError as ve:
            assert True
class TestSIRT(unittest.TestCase):
    def test_SIRT(self):
        print ("Test CGLS")
        #ig = ImageGeometry(124,153,154)
        ig = ImageGeometry(10,2)
        numpy.random.seed(2)
        initial = ig.allocate(0.)
        b = ig.allocate('random')
        # b = initial.copy()
        # fill with random numbers
        # b.fill(numpy.random.random(initial.shape))
        # b = ig.allocate()
        # bdata = numpy.reshape(numpy.asarray([i for i in range(20)]), (2,10))
        # b.fill(bdata)
        identity = IdentityOperator(ig)
        
        alg = SIRT(initial=initial, operator=identity, data=b)
        alg.max_iteration = 200
        alg.run(20, verbose=True)
        np.testing.assert_array_almost_equal(alg.x.as_array(), b.as_array())
        
        alg2 = SIRT(initial=initial, operator=identity, data=b, upper=0.3)
        alg2.max_iteration = 200
        alg2.run(20, verbose=True)
        # equal 
        try:
            numpy.testing.assert_equal(alg2.get_output().max(), 0.3)
            print ("Equal OK, returning")
            return
        except AssertionError as ae:
            print ("Not equal, trying almost equal")
        # almost equal to 7 digits or less
        try:
            numpy.testing.assert_almost_equal(alg2.get_output().max(), 0.3)
            print ("Almost Equal OK, returning")
            return
        except AssertionError as ae:
            print ("Not almost equal, trying less")
        numpy.testing.assert_array_less(alg2.get_output().max(), 0.3)

        # self.assertLessEqual(alg2.get_output().max(), 0.3)
	# maybe we could add a test to compare alg.get_output() when < upper bound is 
	# the same as alg2.get_output() and otherwise 0.3
    
class TestSPDHG(unittest.TestCase):

    @unittest.skipUnless(has_astra, "cil-astra not available")
    def test_SPDHG_vs_PDHG_implicit(self):
        
        data = dataexample.SIMPLE_PHANTOM_2D.get(size=(128,128))

        ig = data.geometry
        ig.voxel_size_x = 0.1
        ig.voxel_size_y = 0.1
            
        detectors = ig.shape[0]
        angles = np.linspace(0, np.pi, 90)
        ag = AcquisitionGeometry('parallel','2D',angles, detectors, pixel_size_h = 0.1, angle_unit='radian')
        # Select device
        dev = 'cpu'
    
        Aop = AstraProjectorSimple(ig, ag, dev)
        
        sin = Aop.direct(data)
        # Create noisy data. Apply Gaussian noise
        noises = ['gaussian', 'poisson']
        noise = noises[1]
        noisy_data = ag.allocate()
        if noise == 'poisson':
            np.random.seed(10)
            scale = 20
            eta = 0
            noisy_data.fill(np.random.poisson(scale * (eta + sin.as_array()))/scale)
        elif noise == 'gaussian':
            np.random.seed(10)
            n1 = np.random.normal(0, 0.1, size = ag.shape)
            noisy_data.fill(n1 + sin.as_array())
            
        else:
            raise ValueError('Unsupported Noise ', noise)
    
           
        # Create BlockOperator
        operator = Aop 
        f = KullbackLeibler(b=noisy_data)        
        alpha = 0.005
        g =  alpha * TotalVariation(50, 1e-4, lower=0)   
        normK = operator.norm()
            
        #% 'implicit' PDHG, preconditioned step-sizes
        tau_tmp = 1.
        sigma_tmp = 1.
        tau = sigma_tmp / operator.adjoint(tau_tmp * operator.range_geometry().allocate(1.))
        sigma = tau_tmp / operator.direct(sigma_tmp * operator.domain_geometry().allocate(1.))
    #    initial = operator.domain_geometry().allocate()
    
    #    # Setup and run the PDHG algorithm
        pdhg = PDHG(f=f,g=g,operator=operator, tau=tau, sigma=sigma,
                    max_iteration = 1000,
                    update_objective_interval = 500)
        pdhg.run(very_verbose = True)
           
        subsets = 10
        size_of_subsets = int(len(angles)/subsets)
        # take angles and create uniform subsets in uniform+sequential setting
        list_angles = [angles[i:i+size_of_subsets] for i in range(0, len(angles), size_of_subsets)]
        # create acquisitioin geometries for each the interval of splitting angles
        list_geoms = [AcquisitionGeometry('parallel','2D',list_angles[i], detectors, pixel_size_h = 0.1, angle_unit='radian') 
                        for i in range(len(list_angles))]
        # create with operators as many as the subsets
        A = BlockOperator(*[AstraProjectorSimple(ig, list_geoms[i], dev) for i in range(subsets)])
        ## number of subsets
        #(sub2ind, ind2sub) = divide_1Darray_equally(range(len(A)), subsets)
        #
        ## acquisisiton data
        g = BlockDataContainer(*[AcquisitionData(noisy_data.as_array()[i:i+size_of_subsets,:])
                                    for i in range(0, len(angles), size_of_subsets)])
        ## block function
        F = BlockFunction(*[KullbackLeibler(b=g[i]) for i in range(subsets)]) 
        G = alpha * TotalVariation(50, 1e-4, lower=0) 
    
        prob = [1/len(A)]*len(A)
        spdhg = SPDHG(f=F,g=G,operator=A, 
                    max_iteration = 1000,
                    update_objective_interval=200, prob = prob)
        spdhg.run(1000, very_verbose = True)
        from cil.utilities.quality_measures import mae, mse, psnr
        qm = (mae(spdhg.get_output(), pdhg.get_output()),
            mse(spdhg.get_output(), pdhg.get_output()),
            psnr(spdhg.get_output(), pdhg.get_output())
            )
        print ("Quality measures", qm)
            
        np.testing.assert_almost_equal( mae(spdhg.get_output(), pdhg.get_output()), 
                                            0.000335, decimal=3)
        np.testing.assert_almost_equal( mse(spdhg.get_output(), pdhg.get_output()), 
                                            5.51141e-06, decimal=3) 
        
    @unittest.skipUnless(has_astra, "ccpi-astra not available")
    def test_SPDHG_vs_PDHG_explicit(self):
        data = dataexample.SIMPLE_PHANTOM_2D.get(size=(128,128))
        print ("here")
        ig = data.geometry
        ig.voxel_size_x = 0.1
        ig.voxel_size_y = 0.1
            
        detectors = ig.shape[0]
        angles = np.linspace(0, np.pi, 180)
        ag = AcquisitionGeometry('parallel','2D',angles, detectors, pixel_size_h = 0.1, angle_unit='radian')
        # Select device
        dev = 'cpu'

        Aop = AstraProjectorSimple(ig, ag, dev)
        
        sin = Aop.direct(data)
        # Create noisy data. Apply Gaussian noise
        noises = ['gaussian', 'poisson']
        noise = noises[1]
        if noise == 'poisson':
            scale = 5
            noisy_data = scale * applynoise.poisson(sin/scale, seed=10)
            # np.random.seed(10)
            # scale = 5
            # eta = 0
            # noisy_data = AcquisitionData(np.random.poisson( scale * (eta + sin.as_array()))/scale, ag)
        elif noise == 'gaussian':
            noisy_data = noise.gaussian(sin, var=0.1, seed=10)
            # np.random.seed(10)
            # n1 = np.random.normal(0, 0.1, size = ag.shape)
            # noisy_data = AcquisitionData(n1 + sin.as_array(), ag)
            
        else:
            raise ValueError('Unsupported Noise ', noise)
        
        #%% 'explicit' SPDHG, scalar step-sizes
        subsets = 10
        size_of_subsets = int(len(angles)/subsets)
        # create Gradient operator
        op1 = GradientOperator(ig)
        # take angles and create uniform subsets in uniform+sequential setting
        list_angles = [angles[i:i+size_of_subsets] for i in range(0, len(angles), size_of_subsets)]
        # create acquisitioin geometries for each the interval of splitting angles
        list_geoms = [AcquisitionGeometry('parallel','2D',list_angles[i], detectors, pixel_size_h = 0.1, angle_unit='radian') 
        for i in range(len(list_angles))]
        # create with operators as many as the subsets
        A = BlockOperator(*[AstraProjectorSimple(ig, list_geoms[i], dev) for i in range(subsets)] + [op1])
        ## number of subsets
        #(sub2ind, ind2sub) = divide_1Darray_equally(range(len(A)), subsets)
        #
        ## acquisisiton data
        g = BlockDataContainer(*[AcquisitionData(noisy_data.as_array()[i:i+size_of_subsets,:]) for i in range(0, len(angles), size_of_subsets)])
        alpha = 0.5
        ## block function
        F = BlockFunction(*[*[KullbackLeibler(b=g[i]) for i in range(subsets)] + [alpha * MixedL21Norm()]]) 
        G = IndicatorBox(lower=0)
        print ("here")
        prob = [1/(2*subsets)]*(len(A)-1) + [1/2]
        spdhg = SPDHG(f=F,g=G,operator=A, 
                    max_iteration = 1000,
                    update_objective_interval=200, prob = prob)
        spdhg.run(1000, very_verbose = True)

        #%% 'explicit' PDHG, scalar step-sizes
        op1 = GradientOperator(ig)
        op2 = Aop
        # Create BlockOperator
        operator = BlockOperator(op1, op2, shape=(2,1) ) 
        f2 = KullbackLeibler(b=noisy_data)  
        g =  IndicatorBox(lower=0)    
        normK = operator.norm()
        sigma = 1/normK
        tau = 1/normK
            
        f1 = alpha * MixedL21Norm() 
        f = BlockFunction(f1, f2)   
        # Setup and run the PDHG algorithm
        pdhg = PDHG(f=f,g=g,operator=operator, tau=tau, sigma=sigma)
        pdhg.max_iteration = 1000
        pdhg.update_objective_interval = 200
        pdhg.run(1000, very_verbose = True)

        #%% show diff between PDHG and SPDHG
        # plt.imshow(spdhg.get_output().as_array() -pdhg.get_output().as_array())
        # plt.colorbar()
        # plt.show()

        from cil.utilities.quality_measures import mae, mse, psnr
        qm = (mae(spdhg.get_output(), pdhg.get_output()),
            mse(spdhg.get_output(), pdhg.get_output()),
            psnr(spdhg.get_output(), pdhg.get_output())
            )
        print ("Quality measures", qm)
        np.testing.assert_almost_equal( mae(spdhg.get_output(), pdhg.get_output()),
         0.00150 , decimal=3)
        np.testing.assert_almost_equal( mse(spdhg.get_output(), pdhg.get_output()), 
        1.68590e-05, decimal=3)
    
    @unittest.skipUnless(has_astra, "ccpi-astra not available")
    def test_SPDHG_vs_SPDHG_explicit_axpby(self):
        data = dataexample.SIMPLE_PHANTOM_2D.get(size=(128,128))
        print ("test_SPDHG_vs_SPDHG_explicit_axpby here")
        ig = data.geometry
        ig.voxel_size_x = 0.1
        ig.voxel_size_y = 0.1
            
        detectors = ig.shape[0]
        angles = np.linspace(0, np.pi, 180)
        ag = AcquisitionGeometry('parallel','2D',angles, detectors, pixel_size_h = 0.1, angle_unit='radian')
        # Select device
        # device = input('Available device: GPU==1 / CPU==0 ')
        # if device=='1':
        #     dev = 'gpu'
        # else:
        #     dev = 'cpu'
        dev = 'cpu'

        Aop = AstraProjectorSimple(ig, ag, dev)
        
        sin = Aop.direct(data)
        # Create noisy data. Apply Gaussian noise
        noises = ['gaussian', 'poisson']
        noise = noises[1]
        if noise == 'poisson':
            np.random.seed(10)
            scale = 5
            eta = 0
            noisy_data = AcquisitionData(np.random.poisson( scale * (eta + sin.as_array()))/scale, ag)
        elif noise == 'gaussian':
            np.random.seed(10)
            n1 = np.random.normal(0, 0.1, size = ag.shape)
            noisy_data = AcquisitionData(n1 + sin.as_array(), ag)
            
        else:
            raise ValueError('Unsupported Noise ', noise)
        
        #%% 'explicit' SPDHG, scalar step-sizes
        subsets = 10
        size_of_subsets = int(len(angles)/subsets)
        # create GradientOperator operator
        op1 = GradientOperator(ig)
        # take angles and create uniform subsets in uniform+sequential setting
        list_angles = [angles[i:i+size_of_subsets] for i in range(0, len(angles), size_of_subsets)]
        # create acquisitioin geometries for each the interval of splitting angles
        list_geoms = [AcquisitionGeometry('parallel','2D',list_angles[i], detectors, pixel_size_h = 0.1, angle_unit='radian') 
        for i in range(len(list_angles))]
        # create with operators as many as the subsets
        A = BlockOperator(*[AstraProjectorSimple(ig, list_geoms[i], dev) for i in range(subsets)] + [op1])
        ## number of subsets
        #(sub2ind, ind2sub) = divide_1Darray_equally(range(len(A)), subsets)
        #
        ## acquisisiton data
        g = BlockDataContainer(*[AcquisitionData(noisy_data.as_array()[i:i+size_of_subsets,:]) for i in range(0, len(angles), size_of_subsets)])
        alpha = 0.5
        ## block function
        F = BlockFunction(*[*[KullbackLeibler(b=g[i]) for i in range(subsets)] + [alpha * MixedL21Norm()]]) 
        G = IndicatorBox(lower=0)
        print ("here")
        prob = [1/(2*subsets)]*(len(A)-1) + [1/2]
        algos = []
        algos.append( SPDHG(f=F,g=G,operator=A, 
                    max_iteration = 1000,
                    update_objective_interval=200, prob = prob.copy(), use_axpby=True)
        )
        algos[0].run(1000, very_verbose = True)

        algos.append( SPDHG(f=F,g=G,operator=A, 
                    max_iteration = 1000,
                    update_objective_interval=200, prob = prob.copy(), use_axpby=False)
        )
        algos[1].run(1000, very_verbose = True)
        

        # np.testing.assert_array_almost_equal(algos[0].get_output().as_array(), algos[1].get_output().as_array())
        from cil.utilities.quality_measures import mae, mse, psnr
        qm = (mae(algos[0].get_output(), algos[1].get_output()),
            mse(algos[0].get_output(), algos[1].get_output()),
            psnr(algos[0].get_output(), algos[1].get_output())
            )
        print ("Quality measures", qm)
        assert qm[0] < 0.005
        assert qm[1] < 3.e-05

    
    
    @unittest.skipUnless(has_astra, "ccpi-astra not available")
    def test_PDHG_vs_PDHG_explicit_axpby(self):
        data = dataexample.SIMPLE_PHANTOM_2D.get(size=(128,128))
        print ("test_PDHG_vs_PDHG_explicit_axpby here")
        ig = data.geometry
        ig.voxel_size_x = 0.1
        ig.voxel_size_y = 0.1
            
        detectors = ig.shape[0]
        angles = np.linspace(0, np.pi, 180)
        ag = AcquisitionGeometry('parallel','2D',angles, detectors, pixel_size_h = 0.1, angle_unit='radian')
        
        dev = 'cpu'

        Aop = AstraProjectorSimple(ig, ag, dev)
        
        sin = Aop.direct(data)
        # Create noisy data. Apply Gaussian noise
        noises = ['gaussian', 'poisson']
        noise = noises[1]
        if noise == 'poisson':
            np.random.seed(10)
            scale = 5
            eta = 0
            noisy_data = AcquisitionData(np.random.poisson( scale * (eta + sin.as_array()))/scale, ag)
        elif noise == 'gaussian':
            np.random.seed(10)
            n1 = np.random.normal(0, 0.1, size = ag.shape)
            noisy_data = AcquisitionData(n1 + sin.as_array(), ag)
            
        else:
            raise ValueError('Unsupported Noise ', noise)
         
        
        alpha = 0.5
        op1 = GradientOperator(ig)
        op2 = Aop
        # Create BlockOperator
        operator = BlockOperator(op1, op2, shape=(2,1) ) 
        f2 = KullbackLeibler(b=noisy_data)  
        g =  IndicatorBox(lower=0)    
        normK = operator.norm()
        sigma = 1./normK
        tau = 1./normK
            
        f1 = alpha * MixedL21Norm() 
        f = BlockFunction(f1, f2)   
        # Setup and run the PDHG algorithm
        
        algos = []
        algos.append( PDHG(f=f,g=g,operator=operator, tau=tau, sigma=sigma,  
                    max_iteration = 1000,
                    update_objective_interval=200, use_axpby=True)
        )
        algos[0].run(1000, very_verbose = True)

        algos.append( PDHG(f=f,g=g,operator=operator, tau=tau, sigma=sigma,  
                    max_iteration = 1000,
                    update_objective_interval=200, use_axpby=False)
        )
        algos[1].run(1000, very_verbose = True)
        

        from cil.utilities.quality_measures import mae, mse, psnr
        qm = (mae(algos[0].get_output(), algos[1].get_output()),
            mse(algos[0].get_output(), algos[1].get_output()),
            psnr(algos[0].get_output(), algos[1].get_output())
            )
        print ("Quality measures", qm)
        np.testing.assert_array_less( qm[0], 0.005 )
        np.testing.assert_array_less( qm[1], 3e-05)
        


class PrintAlgo(Algorithm):
    def __init__(self, **kwargs):

        super(PrintAlgo, self).__init__(**kwargs)
        # self.update_objective()
        self.configured = True

    def update(self):
        self.x = - self.iteration
        time.sleep(0.1)
    
    def update_objective(self):
        self.loss.append(self.iteration * self.iteration)

class TestPrint(unittest.TestCase):
    def test_print(self):
        def callback (iteration, objective, solution):
            print("I am being called ", iteration)
        algo = PrintAlgo(update_objective_interval = 10, max_iteration = 1000)

        algo.run(20, verbose=2, print_interval = 2)
        # it 0
        # it 10 
        # it 20
        # --- stop
        algo.run(3, verbose=1, print_interval = 2)
        # it 20
        # --- stop

        algo.run(20, verbose = 1, print_interval = 7)
        # it 20
        # it 30
        # -- stop

        algo.run(20, verbose=True, very_verbose=False)
        algo.run(20, verbose=True, very_verbose=True, print_interval=7, callback=callback)
        print (algo._iteration)
        print (algo.objective)
        np.testing.assert_array_equal([0, 10, 20, 30, 40, 50, 60, 70, 80], algo.iterations)
        np.testing.assert_array_equal([0, 100, 400, 900, 1600, 2500, 3600, 4900, 6400], algo.objective)

