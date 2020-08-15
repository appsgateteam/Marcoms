# -*- coding: utf-8 -*-
# Copyright (C) 2019-present Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import models, api
import odoo


class Language(models.Model):
    _inherit = 'res.lang'

    @api.model
    @odoo.tools.ormcache(skiparg=1)
    def _get_languages_dir(self):
        langs = self.search([('active', '=', True)])
        return dict([(lg.code, lg.direction) for lg in langs])

    @api.multi
    def get_languages_dir(self):
        return self._get_languages_dir()

    @api.multi
    def write(self, vals):
        self._get_languages_dir.clear_cache(self)
        return super(Language, self).write(vals)