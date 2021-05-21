# -*- coding: utf-8 -*- 
# ======================================== 
# Author: wjh 
# Date：2021/1/19 
# FILE: ir_module 
# ========================================
from odoo import api, fields, models, _
from odoo.exceptions import UserError

ACTION_DICT = {
    'view_type': 'form',
    'view_mode': 'form',
    'res_model': 'base.module.upgrade',
    'target': 'new',
    'type': 'ir.actions.act_window',
}


class ModuleModel(models.Model):
    _inherit = 'ir.module.module'

    @api.multi
    def button_immediate_upgrade_only(self):
        """单独模块升级"""
        return self._button_immediate_function(type(self).button_upgrade_only)

    @api.multi
    def button_upgrade_only(self):
        self.update_list()

        todo = list(self)
        i = 0
        while i < len(todo):
            module = todo[i]
            i += 1
            if module.state not in ('installed', 'to upgrade'):
                raise UserError(_("Can not upgrade module '%s'. It is not installed.") % (module.name,))
            self.check_external_dependencies(module.name, 'to upgrade')
            # search parent
        self.browse(module.id for module in todo).write({'state': 'to upgrade'})

        # search children
        to_install = []
        for module in todo:
            for dep in module.dependencies_id:
                if dep.state == 'unknown':
                    raise UserError(_(
                        'You try to upgrade the module %s that depends on the module: %s.\nBut this module is not available in your system.') % (
                                    module.name, dep.name,))
                if dep.state == 'uninstalled':
                    to_install += self.search([('name', '=', dep.name)]).ids

        self.browse(to_install).button_install()
        return dict(ACTION_DICT, name=_('Apply Schedule Upgrade'))