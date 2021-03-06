import sys
import unittest
import numpy
from cil.framework import DataContainer
from cil.framework import ImageData
from cil.framework import AcquisitionData
from cil.framework import ImageGeometry
from cil.framework import AcquisitionGeometry
from timeit import default_timer as timer


try:
    from ccpi.filters import regularisers
    from ccpi.filters.cpu_regularisers import TV_ENERGY
    has_regularisation_toolkit = True
except ImportError as ie:
    # raise ImportError(ie + "\n\n" + 
    #                   "This plugin requires the additional package ccpi-regularisation\n" +
    #                   "Please install it via conda as ccpi-regularisation from the ccpi channel\n"+
    #                   "Minimal version is 20.04")
    has_regularisation_toolkit = False
print ("has_regularisation_toolkit", has_regularisation_toolkit)

class TestPlugin(unittest.TestCase):
    def setUp(self):
        print ("test plugins")
        pass
    def tearDown(self):
        pass
    @unittest.skipUnless(has_regularisation_toolkit, "Skipping as CCPi Regularisation Toolkit is not installed")
    def test_import_FGP_TV(self):
        try:
            from cil.plugins.ccpi_regularisation.functions.regularisers import FGP_TV
            assert True
        except ModuleNotFoundError as ie:
            print (ie)
            assert False
    @unittest.skipUnless(has_regularisation_toolkit, "Skipping as CCPi Regularisation Toolkit is not installed")
    def test_import_ROF_TV(self):
        try:
            from cil.plugins.ccpi_regularisation.functions import ROF_TV
            assert True
        except ModuleNotFoundError as ie:
            assert False
    @unittest.skipUnless(has_regularisation_toolkit, "Skipping as CCPi Regularisation Toolkit is not installed")
    def test_import_TGV(self):
        try:
            from cil.plugins.ccpi_regularisation.functions import TGV
            assert True
        except ModuleNotFoundError as ie:
            assert False
    @unittest.skipUnless(has_regularisation_toolkit, "Skipping as CCPi Regularisation Toolkit is not installed")
    def test_import_LLT_ROF(self):
        try:
            from cil.plugins.ccpi_regularisation.functions import LLT_ROF
            assert True
        except ModuleNotFoundError as ie:
            assert False
    @unittest.skipUnless(has_regularisation_toolkit, "Skipping as CCPi Regularisation Toolkit is not installed")
    def test_import_FGP_dTV(self):
        try:
            from cil.plugins.ccpi_regularisation.functions import FGP_dTV
            assert True
        except ModuleNotFoundError as ie:
            assert False
    @unittest.skipUnless(has_regularisation_toolkit, "Skipping as CCPi Regularisation Toolkit is not installed")
    def test_import_SB_TV(self):
        try:
            from cil.plugins.ccpi_regularisation.functions import SB_TV
            assert True
        except ModuleNotFoundError as ie:
            assert False
    @unittest.skipUnless(has_regularisation_toolkit, "Skipping as CCPi Regularisation Toolkit is not installed")
    def test_import_TNV(self):
        try:
            from cil.plugins.ccpi_regularisation.functions import TNV
            assert True
        except ModuleNotFoundError as ie:
            assert False