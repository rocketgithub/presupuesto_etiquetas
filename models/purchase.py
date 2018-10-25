# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
import logging

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    por_ejecutar = fields.Monetary(string='Por ejecutar')

    def revisar_etiquetas(self, budget_analytic_tag):
        for tag in self.analytic_tag_ids:
            if tag.id == budget_analytic_tag.id:
                return True
        return False

    @api.onchange('account_analytic_id', 'analytic_tag_ids', 'product_id')
    def onchange_account_analytic_id(self):
        if self.account_analytic_id and self.product_id:
            lineas = self.env['crossovered.budget.lines'].search([('date_from', '<=', datetime.datetime.strptime(self.date_order, "%Y-%m-%d %H:%M:%S").date()),('date_to', '>=', datetime.datetime.strptime(self.date_order, "%Y-%m-%d %H:%M:%S").date()),('analytic_account_id', '=', self.account_analytic_id.id)])
            if lineas:
                self.por_ejecutar = 0
                for linea in lineas:
                    if self.revisar_etiquetas(linea.analytic_tag_id):
                        for account_id in linea.general_budget_id.account_ids:
                            if self.product_id.property_account_expense_id.id == account_id.id:
                                self.por_ejecutar = lineas[0].planned_amount - abs(lineas[0].practical_amount)
