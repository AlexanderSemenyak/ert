#  Copyright (C) 2012  Equinor ASA, Norway.
#
#  The file 'site_config.py' is part of ERT - Ensemble based Reservoir Tool.
#
#  ERT is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  ERT is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.
#
#  See the GNU General Public License at <http://www.gnu.org/licenses/gpl.html>
#  for more details.
from os.path import isfile

from cwrap import BaseCClass
from res import ResPrototype


class SiteConfig(BaseCClass):
    TYPE_NAME = "site_config"
    _alloc                  = ResPrototype("void* site_config_alloc(config_content)", bind=False)
    _alloc_load_user_config = ResPrototype("void* site_config_alloc_load_user_config(char*)", bind=False)
    _free                   = ResPrototype("void site_config_free( site_config )")
    _get_installed_jobs     = ResPrototype("ext_joblist_ref site_config_get_installed_jobs(site_config)")
    _get_license_root_path  = ResPrototype("char* site_config_get_license_root_path(site_config)")
    _set_license_root_path  = ResPrototype("void site_config_set_license_root_path(site_config, char*)")
    _get_path_variables     = ResPrototype("stringlist_ref site_config_get_path_variables(site_config)")
    _get_path_values        = ResPrototype("stringlist_ref site_config_get_path_values(site_config)")
    _clear_pathvar          = ResPrototype("void site_config_clear_pathvar(site_config)")
    _update_pathvar         = ResPrototype("void site_config_update_pathvar(site_config, char*, char*)")
    _get_location           = ResPrototype("char* site_config_get_location(site_config)")
    _get_config_file        = ResPrototype("char* site_config_get_config_file(site_config)")
    _get_umask              = ResPrototype("int site_config_get_umask(site_config)")


    def __init__(self, user_config_file=None, config_content=None):

        if user_config_file is not None:
            if not isfile(user_config_file):
                raise IOError('No such configuration file "%s".' % user_config_file)

            c_ptr = self._alloc_load_user_config(user_config_file)
            if c_ptr:
                super(SiteConfig, self).__init__(c_ptr)
            else:
                raise ValueError('Failed to construct SiteConfig instance from config file %s.' % user_config_file)

        else:
            c_ptr = self._alloc(config_content)

            if c_ptr is None:
                raise ValueError('Failed to construct SiteConfig instance.')

            super(SiteConfig, self).__init__(c_ptr)


    def __repr__(self):
        return "Site Config loaded from %s" % self.config_file

    @property
    def config_file(self):
        return self._get_config_file()

    def get_path_variables(self):
        """ @rtype: StringList """
        return self._get_path_variables().setParent(self)

    def get_path_values(self):
        """ @rtype: StringList """
        return self._get_path_values().setParent(self)

    def clear_pathvar(self):
        self._clear_pathvar(  )

    def update_pathvar(self, pathvar, value):
        self._update_pathvar( pathvar, value)

    def get_installed_jobs(self):
        """ @rtype: ExtJoblist """
        return self._get_installed_jobs().setParent(self)

    def get_license_root_path(self):
        """ @rtype: str """
        return self._get_license_root_path( )

    def set_license_root_pathmax_submit(self, path):
        self._set_license_root_path( path)

    def getLocation(self):
        """ @rtype: str """
        return self._get_location()

    def free(self):
        self._free()

    @property
    def umask(self):
        return self._get_umask()
