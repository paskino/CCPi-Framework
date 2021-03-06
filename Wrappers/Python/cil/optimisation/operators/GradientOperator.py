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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from cil.optimisation.operators import LinearOperator
from cil.optimisation.operators import FiniteDifferenceOperator
from cil.framework import ImageGeometry, BlockGeometry
import warnings
from cil.utilities.multiprocessing import NUM_THREADS
import numpy as np

NEUMANN = 'Neumann'
PERIODIC = 'Periodic'
C = 'c'
NUMPY = 'numpy'
CORRELATION_SPACE = "Space"
CORRELATION_SPACECHANNEL = "SpaceChannels"

class GradientOperator(LinearOperator):


    r'''Gradient Operator: Computes first-order forward/backward differences on 
        2D, 3D, 4D ImageData under Neumann/Periodic boundary conditions
    
    :param gm_domain: Set up the domain of the function
    :type gm_domain: `ImageGeometry`
    :param bnd_cond: Set the boundary conditions to use 'Neumann' or 'Periodic', defaults to 'Neumann'
    :type bnd_cond: str, optional    
    
    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *correlation* (``str``) --
          'Space' or 'SpaceChannels', defaults to 'Space'
        * *backend* (``str``) --
          'c' or 'numpy', defaults to 'c' if correlation is 'SpaceChannels' or channels = 1
        * *num_threads* (``int``) --
          If backend is 'c' specify the number of threads to use. Default is number of cpus/2          
                 
                 
        Example (2D): 
        .. math::
        
          \nabla : X -> Y \\
          u\in X, \nabla(u) = [\partial_{y} u, \partial_{x} u] \\
          u^{*}\in Y, \nabla^{*}(u^{*}) = \partial_{y} v1 + \partial_{x} v2
            

    '''

    #kept here for backwards compatability
    CORRELATION_SPACE = CORRELATION_SPACE
    CORRELATION_SPACECHANNEL = CORRELATION_SPACECHANNEL

    def __init__(self, domain_geometry, method = 'forward', bnd_cond = 'Neumann', **kwargs):
        """Constructor method
        """        
        
        backend = kwargs.get('backend',C)

        correlation = kwargs.get('correlation',CORRELATION_SPACE)

        if correlation == CORRELATION_SPACE and domain_geometry.channels > 1:
            #numpy implementation only for now
            backend = NUMPY
            warnings.warn("Warning: correlation='Space' on multi-channel dataset will use `numpy` backend")
           
        if method != 'forward':
            backend = NUMPY
            warnings.warn("Warning: method = {} implemented on `numpy` backend. Other methods are backward/centered.".format(method))            
            
        if backend == NUMPY:
            self.operator = Gradient_numpy(domain_geometry, bnd_cond=bnd_cond, **kwargs)
        else:
            self.operator = Gradient_C(domain_geometry, bnd_cond=bnd_cond, **kwargs)
        
        super(GradientOperator, self).__init__(domain_geometry=domain_geometry, 
                                       range_geometry=self.operator.range_geometry()) 

        self.gm_range = self.range_geometry()
        self.gm_domain = self.domain_geometry()


    def direct(self, x, out=None):
        """Computes the first-order forward differences

        :param x: Image data
        :type x: `ImageData`
        :param out: pre-allocated output memory to store result
        :type out: `BlockDataContainer`, optional        
        :return: result data if not passed as parameter
        :rtype: `BlockDataContainer`
        """        
        return self.operator.direct(x, out=out)
        
        
    def adjoint(self, x, out=None):
        """Computes the first-order backward differences

        :param x: Gradient images for each dimension in ImageGeometry domain
        :type x: `BlockDataContainer`
        :param out: pre-allocated output memory to store result
        :type out: `ImageData`, optional      
        :return: result data if not passed as parameter
        :rtype: `ImageData`
        """            
        return self.operator.adjoint(x, out=out)

class Gradient_numpy(LinearOperator):
    
    def __init__(self, domain_geometry, method = 'forward', bnd_cond = 'Neumann', **kwargs):
        '''creator
        
        :param gm_domain: domain of the operator
        :type gm_domain: :code:`AcquisitionGeometry` or :code:`ImageGeometry`
        :param bnd_cond: boundary condition, either :code:`Neumann` or :code:`Periodic`.
        :type bnd_cond: str, optional, default :code:`Neumann`
        :param correlation: optional, :code:`SpaceChannel` or :code:`Space`
        :type correlation: str, optional, default :code:`Space`
        '''                
        
        self.size_dom_gm = len(domain_geometry.shape)         
        self.correlation = kwargs.get('correlation',CORRELATION_SPACE)        
        self.bnd_cond = bnd_cond 
        
        # Call FiniteDiff operator 
        self.method = method
        self.FD = FiniteDifferenceOperator(domain_geometry, direction = 0, method = self.method, bnd_cond = self.bnd_cond)
                
        
        if self.correlation==CORRELATION_SPACE:
            
            if domain_geometry.channels > 1:
                
                range_geometry = BlockGeometry(*[domain_geometry for _ in range(domain_geometry.length-1)] )

                if self.size_dom_gm == 4:
                    # 3D + Channel
                    expected_order = [ImageGeometry.CHANNEL, ImageGeometry.VERTICAL, ImageGeometry.HORIZONTAL_Y, ImageGeometry.HORIZONTAL_X]

                else:
                    # 2D + Channel
                    expected_order = [ImageGeometry.CHANNEL, ImageGeometry.HORIZONTAL_Y, ImageGeometry.HORIZONTAL_X]

                order = domain_geometry.get_order_by_label(domain_geometry.dimension_labels, expected_order)
                
                self.ind = order[1:]
                
            else:
                # no channel info
                range_geometry = BlockGeometry(*[domain_geometry for _ in range(domain_geometry.length) ] )
                if self.size_dom_gm == 3:
                    # 3D
                    expected_order = [ImageGeometry.VERTICAL, ImageGeometry.HORIZONTAL_Y, ImageGeometry.HORIZONTAL_X]
#                    self.voxel_size_order = [domain_geometry.voxel_size_z, domain_geometry.voxel_size_y, domain_geometry.voxel_size_x ]                    
                    
                else:
                    # 2D
                    expected_order = [ImageGeometry.HORIZONTAL_Y, ImageGeometry.HORIZONTAL_X]    

                self.ind = domain_geometry.get_order_by_label(domain_geometry.dimension_labels, expected_order)
                
        elif self.correlation==CORRELATION_SPACECHANNEL:
            
            if domain_geometry.channels > 1:
                range_geometry = BlockGeometry(*[domain_geometry for _ in range(domain_geometry.length)])
                self.ind = range(domain_geometry.length)                
            else:
                raise ValueError('No channels to correlate')
                
        self.voxel_size_order = domain_geometry.spacing                
         
        super(Gradient_numpy, self).__init__(domain_geometry = domain_geometry, 
                                             range_geometry = range_geometry) 
        
        print("Initialised GradientOperator with numpy backend")               
        
    def direct(self, x, out=None):        
                
         if out is not None:
            
             for i in range(self.range_geometry().shape[0]):
                 self.FD.direction = self.ind[i]
                 self.FD.voxel_size = self.voxel_size_order[i]
                 self.FD.direct(x, out = out[i])
         else:
             tmp = self.range_geometry().allocate()        
             for i in range(tmp.shape[0]):
                 self.FD.direction = self.ind[i]
                 self.FD.voxel_size = self.voxel_size_order[i]
                 tmp.get_item(i).fill(self.FD.direct(x))
             return tmp    
        
    def adjoint(self, x, out=None):

        if out is not None:

            tmp = self.domain_geometry().allocate()            
            for i in range(x.shape[0]):
                self.FD.direction=self.ind[i] 
                self.FD.voxel_size = self.voxel_size_order[i]
                self.FD.adjoint(x.get_item(i), out = tmp)
                if i == 0:
                    out.fill(tmp)
                else:
                    out += tmp
        else:            
            tmp = self.domain_geometry().allocate()
            for i in range(x.shape[0]):
                self.FD.direction=self.ind[i]
                self.FD.voxel_size = self.voxel_size_order[i]
                tmp += self.FD.adjoint(x.get_item(i))
            return tmp    

import ctypes, platform
from ctypes import util
# check for the extension
if platform.system() == 'Linux':
    dll = 'libcilacc.so'
elif platform.system() == 'Windows':
    dll = 'cilacc.dll'
elif platform.system() == 'Darwin':
    dll = 'libcilacc.dylib'
else:
    raise ValueError('Not supported platform, ', platform.system())

dll_path = util.find_library(dll)
cilacc = ctypes.cdll.LoadLibrary(dll_path)

c_float_p = ctypes.POINTER(ctypes.c_float)

cilacc.openMPtest.restypes = ctypes.c_int32
cilacc.openMPtest.argtypes = [ctypes.c_int32]

cilacc.fdiff4D.argtypes = [ctypes.POINTER(ctypes.c_float),
                       ctypes.POINTER(ctypes.c_float),
                       ctypes.POINTER(ctypes.c_float),
                       ctypes.POINTER(ctypes.c_float),
                       ctypes.POINTER(ctypes.c_float),
                       ctypes.c_long,
                       ctypes.c_long,
                       ctypes.c_long,
                       ctypes.c_long,
                       ctypes.c_int32,
                       ctypes.c_int32,
                       ctypes.c_int32]

cilacc.fdiff3D.argtypes = [ctypes.POINTER(ctypes.c_float),
                       ctypes.POINTER(ctypes.c_float),
                       ctypes.POINTER(ctypes.c_float),
                       ctypes.POINTER(ctypes.c_float),
                       ctypes.c_long,
                       ctypes.c_long,
                       ctypes.c_long,
                       ctypes.c_int32,
                       ctypes.c_int32,
                       ctypes.c_int32]

cilacc.fdiff2D.argtypes = [ctypes.POINTER(ctypes.c_float),
                       ctypes.POINTER(ctypes.c_float),
                       ctypes.POINTER(ctypes.c_float),
                       ctypes.c_long,
                       ctypes.c_long,
                       ctypes.c_int32,
                       ctypes.c_int32,
                       ctypes.c_int32]


class Gradient_C(LinearOperator):
    
    '''Finite Difference Operator:
            
            Computes first-order forward/backward differences 
                     on 2D, 3D, 4D ImageData
                     under Neumann/Periodic boundary conditions'''

    def __init__(self, gm_domain, gm_range=None, bnd_cond = NEUMANN, **kwargs):

        self.num_threads = kwargs.get('num_threads',NUM_THREADS)

        self.gm_domain = gm_domain
        self.gm_range = gm_range
        
        #default is 'Neumann'
        self.bnd_cond = 0
        
        if bnd_cond == PERIODIC:
            self.bnd_cond = 1
        
        # Domain Geometry = Range Geometry if not stated
        if self.gm_range is None:
            self.gm_range = BlockGeometry(*[gm_domain for _ in range(len(gm_domain.shape))])
        
        if len(gm_domain.shape) == 4:
            # Voxel size wrt to channel direction == 1.0
            self.fd = cilacc.fdiff4D
        elif len(gm_domain.shape) == 3:
            self.fd = cilacc.fdiff3D
        elif len(gm_domain.shape) == 2:
            self.fd = cilacc.fdiff2D
        else:
            raise ValueError('Number of dimensions not supported, expected 2, 3 or 4, got {}'.format(len(gm_domain.shape)))
            
        self.voxel_size_order = list(self.gm_domain.spacing)
        super(Gradient_C, self).__init__(domain_geometry=self.gm_domain, 
                                             range_geometry=self.gm_range) 
        print("Initialised GradientOperator with C backend running with ", cilacc.openMPtest(self.num_threads)," threads")               

    @staticmethod 
    def datacontainer_as_c_pointer(x):
        ndx = x.as_array()
        return ndx, ndx.ctypes.data_as(c_float_p)

    @staticmethod 
    def ndarray_as_c_pointer(ndx):
        return ndx.ctypes.data_as(c_float_p)
        
    def direct(self, x, out=None):
        ndx = np.asarray(x.as_array(), dtype=np.float32)
        #ndx , x_p = Gradient_C.datacontainer_as_c_pointer(x)
        x_p = Gradient_C.ndarray_as_c_pointer(ndx)
        
        return_val = False
        if out is None:
            out = self.gm_range.allocate(None)
            return_val = True
        ndout = [el.as_array() for el in out.containers]

        #pass list of all arguments
        #arg1 = [Gradient_C.datacontainer_as_c_pointer(out.get_item(i))[1] for i in range(self.gm_range.shape[0])]
        arg1 = [Gradient_C.ndarray_as_c_pointer(ndout[i]) for i in range(self.gm_range.shape[0])]
        arg2 = [el for el in x.shape]
        args = arg1 + arg2 + [self.bnd_cond, 1, self.num_threads]
        self.fd(x_p, *args)
        
        for i in range(len(ndout)):
            out.get_item(i).fill(ndout[i])

        if any(elem != 1.0 for elem in self.voxel_size_order):
            out /= self.voxel_size_order
#        out /= self.voxel_size_order
        
        if return_val is True:
            return out        

    def adjoint(self, x, out=None):
        
        return_val = False
        if out is None:
            out = self.gm_domain.allocate(None)
            return_val = True
        ndout = out.as_array()
        

        # ndout, out_p = Gradient_C.datacontainer_as_c_pointer(out)
        out_p = Gradient_C.ndarray_as_c_pointer(ndout)
        
               
        
        if any(elem != 1.0 for elem in self.voxel_size_order):
            tmp = x/self.voxel_size_order
        else:
            tmp = x
        ndx = [el.as_array() for el in tmp.containers]
        
        #arg1 = [Gradient_C.datacontainer_as_c_pointer(tmp.get_item(i))[1] for i in range(self.gm_range.shape[0])]
        arg1 = [Gradient_C.ndarray_as_c_pointer(ndx[i]) for i in range(self.gm_range.shape[0])]
        arg2 = [el for el in out.shape]
        args = arg1 + arg2 + [self.bnd_cond, 0, self.num_threads]

        self.fd(out_p, *args)
        out.fill(ndout)

        if return_val is True:
            return out

       
