import os
import unittest
import yaml
from unittest import TestCase
from app.app import App
unittest.TestLoader.sortTestMethodsUsing = None

class AppTest(TestCase):

    def test_no_yaml(self):
        """Testing that a new config.yaml gets created if it isn't present
        """
        path = '{}/tests/dirs/test_no_yaml'.format(os.getcwd())
        conf_path = '{}/config.yaml'.format(path)
        
        # remove any present config file at path
        try:
            os.remove(conf_path)
        except:
            pass

        # create directory path if non existent
        try:
            os.makedirs(path)
        except OSError:
            print('Could not make directories')

        # move to create directory path
        try:
            os.chdir(path)
        except OSError:
            print('Could not change path to {}'.path)

        # run __init__ with no config file
        app = App()
        self.assertTrue(os.path.isfile(conf_path))
        
        test_dict = {}
        with open(conf_path, 'r') as handle:
            test_dict = yaml.full_load(handle)
        
        self.assertEqual(test_dict['yaml_path'], conf_path)
        self.assertEqual(test_dict['root'], os.getcwd())


    def test_good_root(self):
        '''Test
        '''
        path = '/home/smadonna/Downloads'
        app = App(path)
        self.assertEqual(App._config['root'], path)
        
        test_dict = {}
        with open('config.yaml', 'r') as handle:
            test_dict = yaml.full_load(handle)
        self.assertEqual(test_dict['root'], path)

        self.assertEqual(os.getcwd(), path)
