# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
import logging

class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    analytic_tag_id = fields.Many2one('account.analytic.tag', string='Etiqueta Analitica')
    
    def _compute_practical_amount(self):
        for line in self:
            result = 0.0
            acc_ids = line.general_budget_id.account_ids.ids
            date_to = self.env.context.get('wizard_date_to') or line.date_to
            date_from = self.env.context.get('wizard_date_from') or line.date_from
            if line.analytic_account_id.id:
                self.env.cr.execute("""
                    SELECT id, amount
                    FROM account_analytic_line
                    WHERE account_id=%s
                        AND (date between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd'))
                        AND general_account_id=ANY(%s)""",
                (line.analytic_account_id.id, date_from, date_to, acc_ids,))
                
                fetch_lines = self._cr.fetchall()
                for id, amount in fetch_lines:
                    if line.analytic_tag_id:
                        self._cr.execute("""\
                            SELECT      tag_id
                            FROM        account_analytic_line_tag_rel
                            WHERE       line_id = %s
                            AND         tag_id = %s
                            """, (id, line.analytic_tag_id.id))
                   
                        if len(self._cr.fetchall()) != 0:
                            result += amount
                    else:
                        result += amount
            line.practical_amount = result
