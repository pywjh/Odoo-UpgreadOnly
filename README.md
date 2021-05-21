# Odoo-UpgreadOnly
odoo模块只升级当前模块，不牵连父级模块

## 只升级当前模块，继承的模块不升级

### 场景：
有一个继承模块，继承了好多别的打模块，那些模块内容庞大，但是我只是修改了继承模块的一点xml的话，升级会连同父级模块一同升级，有时会耗费很多时间
### 思路：
肯定实现从odoo自带的升级功能入手，先看了odoo对应的`button_upgrade`方法，发现其实很简单，他的逻辑就是针对你要升级的模块，再向上找他的父级模块，去重遍历以此升级。所以我只要再做一个按钮，将他的再上级模块的逻辑去掉就可以了
### 代码实现：
先来看看odoo自带的源码吧
```python
    @assert_log_admin_access
    @api.multi
    def button_upgrade(self):
        Dependency = self.env['ir.module.module.dependency']
        self.update_list()

        todo = list(self)  # 要升级的模块列表
        i = 0
        while i < len(todo):
            module = todo[i]
            i += 1
            if module.state not in ('installed', 'to upgrade'):
                raise UserError(_("Can not upgrade module '%s'. It is not installed.") % (module.name,))
            self.check_external_dependencies(module.name, 'to upgrade')
            for dep in Dependency.search([('name', '=', module.name)]):  # 这里开始找升级模型对应的父级模型✨✨✨
                if dep.module_id.state == 'installed' and dep.module_id not in todo:  # 如果是安装状态并且不再待升级列表的，加加入进去✨✨✨
                    todo.append(dep.module_id)

        self.browse(module.id for module in todo).write({'state': 'to upgrade'})

        to_install = []
        for module in todo:
            for dep in module.dependencies_id:
                if dep.state == 'unknown':
                    raise UserError(_('You try to upgrade the module %s that depends on the module: %s.\nBut this module is not available in your system.') % (module.name, dep.name,))
                if dep.state == 'uninstalled':
                    to_install += self.search([('name', '=', dep.name)]).ids

        self.browse(to_install).button_install()
        return dict(ACTION_DICT, name=_('Apply Schedule Upgrade'))
```
所以看着是不是就很简单了，只要把✨✨✨处的代码去掉就可以了！

为了方便使用，我建了一个新的模块，结构如下：
```txt
.
├── __init__.py
├── __manifest__.py
├── models
│   ├── __init__.py
│   └── ir_module.py
└── views
    └── ir_model_view.xml
```
ir_module.py
```python
# -*- coding: utf-8 -*- 
# ======================================== 
# Author: wjh 
# Date：2021/1/19 
# FILE: ir_module 
# ========================================
from odoo import api, models, _
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
```
ir_model_view.xml
```xml
<odoo>
    <data>
        <record id="UpgradeOnlyForm" model="ir.ui.view">
            <field name="name">应用操作视图继承</field>
            <field name="model">ir.module.module</field>
            <field name="inherit_id" ref="base.module_form" />
            <field name="arch" type="xml">
                <button name="button_immediate_upgrade" position="after">
                    <button name="button_immediate_upgrade_only" states="installed" string="升级当前模块" type="object" class="btn btn-primary"/>
                </button>
            </field>
        </record>
    </data>
</odoo>
```
### 效果图
![只升级当前模块效果图](https://img2020.cnblogs.com/blog/1421031/202105/1421031-20210521103210521-335125556.png)


### 最后
直接附上我的代码吧，下载放入odoo项目中，安装上就可以用了
