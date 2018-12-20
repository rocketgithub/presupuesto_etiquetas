# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
import logging

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    por_ejecutar = fields.Monetary(string='Por ejecutar contabilidad')
    por_ejecutar_compras = fields.Monetary(string='Por ejecutar compras')

    #Esta funcion es llamada desde el onchage, y revisa si la cuenta contable del producto coincide con alguna
    #cuenta contable de la posicion presupuestaria de la linea de presupuesto.
    def revisar_cuentas_contables(self, linea_po, account_ids):
        for account_id in account_ids:
            if linea_po.product_id.property_account_expense_id.id == account_id.id:
                return True
        return False


    #Esta funcion es llamada desde el onchange, y revisa si la etiqueta en la linea del pedido de compra coincide con la
    #etiqueta de una linea del presupuesto.
    #Retorna True si hay una coincidencia, o si la linea del pedido de compra no tiene etiqueta asignada.
    def revisar_etiquetas(self, linea_po, budget_analytic_tag):
        if linea_po.analytic_tag_ids:
            for tag in linea_po.analytic_tag_ids:
                if tag.id == budget_analytic_tag.id:
                    return True
            return False
        else:
            return True


    def sumar_lineas_po_borrador(self, linea_presupuesto):
        lineas_po = self.env['purchase.order.line'].search([('order_id.state', '=', 'draft'), ('date_order', '>=', linea_presupuesto.date_from), ('date_order', '<=', linea_presupuesto.date_to), ('account_analytic_id', '=', self.account_analytic_id.id)])
        res = 0
        for linea in lineas_po:
            if self.revisar_etiquetas(linea, linea_presupuesto.analytic_tag_id):
                if self.revisar_cuentas_contables(linea, linea_presupuesto.general_budget_id.account_ids):
                    res += linea.price_subtotal
        return res


    @api.onchange('account_analytic_id', 'analytic_tag_ids', 'product_id')
    def onchange_account_analytic_id(self):
        if self.account_analytic_id and self.product_id:
            #Hago un search de lineas de presupuesto tomando en cuenta:
            # - Fecha del pedido de compra se encuentre en el rango de fechas de la linea del presupuesto.
            # - La cuenta analitica de la linea del pedido de compra coincida con la cuenta analitica de la linea del presupuesto.
            #Existen otros dos filtros, pero esos se revisan en las funciones revisar_cuentas_contables y revisar_etiquetas.
            lineas = self.env['crossovered.budget.lines'].sudo().search([('date_from', '<=', datetime.datetime.strptime(self.date_order, "%Y-%m-%d %H:%M:%S").date()),('date_to', '>=', datetime.datetime.strptime(self.date_order, "%Y-%m-%d %H:%M:%S").date()),('analytic_account_id', '=', self.account_analytic_id.id)])
            self.por_ejecutar = 0
            self.por_ejecutar_compras = 0
            if lineas:
                for linea in lineas:
                    #En estas dos condiciones se revisan los dos filtros faltantes: revisar_cuentas_contables y revisar_etiquetas.
                    if self.revisar_etiquetas(self, linea.analytic_tag_id):
                        if self.revisar_cuentas_contables(self, linea.general_budget_id.account_ids):
                            sumatoria_lineas_borrador = self.sumar_lineas_po_borrador(linea)
                            self.por_ejecutar_compras = sumatoria_lineas_borrador
                            self.por_ejecutar = abs(linea.planned_amount - linea.practical_amount - sumatoria_lineas_borrador)
