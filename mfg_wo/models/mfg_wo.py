from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import float_compare, float_round
from odoo.addons import decimal_precision as dp


class MrpProductionWorkcenterLine(models.Model):
    _name = 'mrp.workorder'
    _inherit = ['mrp.workorder', 'barcodes.barcode_events_mixin']

    check_ids = fields.One2many('quality.check', 'workorder_id')
    skipped_check_ids = fields.One2many('quality.check', 'workorder_id', domain=[('quality_state', '=', 'none')])
    finished_product_check_ids = fields.Many2many('quality.check', compute='_compute_finished_product_check_ids')
    quality_check_todo = fields.Boolean(compute='_compute_check')
    quality_check_fail = fields.Boolean(compute='_compute_check')
    quality_alert_ids = fields.One2many('quality.alert', 'workorder_id')
    quality_alert_count = fields.Integer(compute="_compute_quality_alert_count")

    current_quality_check_id = fields.Many2one('quality.check', "Current Quality Check", store=True)

    # QC-related fields
    allow_producing_quantity_change = fields.Boolean('Allow Changes to Producing Quantity', default=True)
    component_id = fields.Many2one('product.product', compute='_compute_component_id', readonly=True)
    component_tracking = fields.Selection(related='component_id.tracking', string="Is Component Tracked", readonly=False)
    component_remaining_qty = fields.Float('Remaining Quantity for Component', compute='_compute_component_id', readonly=True,digits=dp.get_precision('Product Unit of Measure'))
    component_uom_id = fields.Many2one('uom.uom', compute='_compute_component_id', string="Component UoM")
    control_date = fields.Datetime(related='current_quality_check_id.control_date', readonly=False)
    is_first_step = fields.Boolean('Is First Step')
    is_last_step = fields.Boolean('Is Last Step')
    is_last_lot = fields.Boolean('Is Last lot', compute='_compute_is_last_lot')
    is_last_unfinished_wo = fields.Boolean('Is Last Work Order To Process', compute='_compute_is_last_unfinished_wo', store=False)
    lot_id = fields.Many2one(related='current_quality_check_id.lot_id', readonly=False)
    move_line_id = fields.Many2one(related='current_quality_check_id.move_line_id', readonly=False)
    note = fields.Html(related='current_quality_check_id.note')
    skip_completed_checks = fields.Boolean('Skip Completed Checks', readonly=True)
    quality_state = fields.Selection(related='current_quality_check_id.quality_state', string="Quality State", readonly=False)
    qty_done = fields.Float(related='current_quality_check_id.qty_done', readonly=False)
    test_type = fields.Char('Test Type', compute='_compute_component_id', readonly=True)
    user_id = fields.Many2one(related='current_quality_check_id.user_id', readonly=False)
    worksheet_page = fields.Integer('Worksheet page')
    picture = fields.Binary(related='current_quality_check_id.picture', readonly=False)

    @api.depends('qty_producing', 'qty_remaining')
    def _compute_is_last_lot(self):
        for wo in self:
            precision = wo.production_id.product_uom_id.rounding
            wo.is_last_lot = float_compare(wo.qty_producing, wo.qty_remaining, precision_rounding=precision) >= 0

    @api.depends('production_id.workorder_ids')
    def _compute_is_last_unfinished_wo(self):
        for wo in self:
            other_wos = wo.production_id.workorder_ids - wo
            other_states = other_wos.mapped(lambda w: w.state == 'done')
            wo.is_last_unfinished_wo = all(other_states)

    @api.depends('check_ids')
    def _compute_finished_product_check_ids(self):
        for wo in self:
            wo.finished_product_check_ids = wo.check_ids.filtered(lambda c: c.finished_product_sequence == wo.qty_produced)

    @api.depends('current_quality_check_id', 'qty_producing')
    def _compute_component_id(self):
        for wo in self.filtered(lambda w: w.state not in ('done', 'cancel')):
            if wo.current_quality_check_id.point_id:
                wo.component_id = wo.current_quality_check_id.point_id.component_id
                wo.test_type = wo.current_quality_check_id.point_id.test_type
            elif wo.current_quality_check_id.component_id:
                wo.component_id = wo.current_quality_check_id.component_id
                wo.test_type = 'register_consumed_materials'
            else:
                wo.test_type = ''
            if wo.test_type == 'register_consumed_materials' and wo.quality_state == 'none':
                if wo.current_quality_check_id.component_is_byproduct:
                    moves = wo.production_id.move_finished_ids.filtered(lambda m: m.state not in ('done', 'cancel') and m.product_id == wo.component_id)
                else:
                    moves = wo.move_raw_ids.filtered(lambda m: m.state not in ('done', 'cancel') and m.product_id == wo.component_id)
                move = moves[:1]
                lines = wo.active_move_line_ids.filtered(lambda l: l.move_id in moves)
                completed_lines = lines.filtered(lambda l: l.lot_id) if wo.component_tracking != 'none' else lines
                wo.component_remaining_qty = float_round(sum(moves.mapped('unit_factor')) * wo.qty_producing - sum(completed_lines.mapped('qty_done')), precision_rounding=move.product_uom.rounding)
                wo.component_uom_id = move.product_uom

    def action_back(self):
        self.ensure_one()
        if self.is_user_working and self.working_state != 'blocked':
            self.button_pending()

    def _create_subsequent_checks(self):
        """ When processing a step with regiter a consumed material
        that's a lot we will some times need to create a new
        intermediate check.
        e.g.: Register 2 product A tracked by SN. We will register one
        with the current checks but we need to generate a second step
        for the second SN. Same for lot if the user wants to use more
        than one lot.
        """
        # Create another quality check if necessary
        parent_id = self.current_quality_check_id
        if parent_id.parent_id:
            parent_id = parent_id.parent_id
        subsequent_substeps = self.env['quality.check'].search([('parent_id', '=', parent_id.id), ('id', '>', self.current_quality_check_id.id)])
        if self.component_remaining_qty > 0 and not subsequent_substeps:
            # Creating quality checks
            quality_check_data = {
                'workorder_id': self.id,
                'product_id': self.product_id.id,
                'parent_id': parent_id.id,
                'component_is_byproduct': parent_id.component_is_byproduct,
                'finished_product_sequence': self.qty_produced,
                'qty_done': self.component_remaining_qty if self.component_tracking != 'serial' else 1.0,
            }
            if self.current_quality_check_id.point_id:
                quality_check_data.update({
                    'point_id': self.current_quality_check_id.point_id.id,
                    'team_id': self.current_quality_check_id.point_id.team_id.id,
                })
            else:
                quality_check_data.update({
                    'component_id': self.current_quality_check_id.component_id.id,
                    'team_id': self.current_quality_check_id.team_id.id,
                })
            self.env['quality.check'].create(quality_check_data)

    def _update_active_move_line(self):
        """ This function is only used when the check is regiter a
        component. It will update the active move lines in order to set
        the lot and the quantity used. Tge active move lines created
        are matched with the real move lines during the
        record_production call.
        Behavior is different when the product is a raw material or a
        finished product.
        - Raw material: try to use the already existing move lines.
        - Finished product: always create a new active move lines since
        they were not automatically generated before.
        If the move line already exists for this check then update it.
        """
        # Get the move lines associated with our component
        moves = self.env['stock.move']
        if self.current_quality_check_id.component_is_byproduct:
            moves |= self.production_id.move_finished_ids.filtered(lambda m: m.state not in ('done', 'cancel') and m.product_id == self.component_id)
        else:
            moves = self.move_raw_ids.filtered(lambda m: m.state not in ('done', 'cancel') and m.product_id == self.component_id)
        move = moves[:1]
        if not move:
            raise UserError(
                _('No valid stock move found for product %s.\n\n'
                  'Stock moves linked to raw materials were probably canceled. '
                  'In order to solve the issue, use the "Update" button next to the "Quantity To Produce" '
                  'in the manufacturing order to regenerate the necessary moves.'
                ) % (self.component_id.display_name)
            )

        lines_without_lots = self.active_move_line_ids.filtered(lambda l: l.move_id in moves and not l.lot_id)
        # Compute the theoretical quantity for the current production
        self.component_remaining_qty -= float_round(self.qty_done, precision_rounding=move.product_uom.rounding)
        # Assign move line to quality check if necessary
        if not self.move_line_id:
            if self.component_tracking == 'none' or self.current_quality_check_id.component_is_byproduct or not lines_without_lots:
                self.move_line_id = self.env['stock.move.line'].create({
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'lot_id': False,
                    'product_uom_qty': 0.0,
                    'product_uom_id': move.product_uom.id,
                    'qty_done': float_round(self.qty_done, precision_rounding=move.product_uom.rounding),
                    'workorder_id': self.id,
                    'done_wo': False,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                })
                self.active_move_line_ids += self.move_line_id
            else:
                self.move_line_id = lines_without_lots[0]
            # If tracked by lot, put the remaining quantity in (only) one move line
            if move.product_id.tracking == 'lot' and not self.current_quality_check_id.component_is_byproduct:
                lines_without_lots[1::].unlink()
                if self.component_remaining_qty > 0:
                    self.move_line_id.copy(default={'qty_done': self.component_remaining_qty})

        # Write the lot and qty to the move line
        self.move_line_id.write({'lot_id': self.lot_id.id, 'qty_done': float_round(self.qty_done, precision_rounding=move.product_uom.rounding)})

    def _next(self, state='pass'):
        """ This function:
        - first: fullfill related move line with right lot and validated quantity.
        - second: Generate new quality check for remaining quantity and link them to the original check.
        - third: Pass to the next check or return a failure message.
        """
        self.ensure_one()
        if self.qty_producing <= 0 or self.qty_producing > self.qty_remaining:
            raise UserError(_('Please ensure the quantity to produce is nonnegative and does not exceed the remaining quantity.'))
        elif self.test_type == 'register_consumed_materials':
            # Form validation
            if self.component_tracking != 'none' and not self.lot_id:
                raise UserError(_('Please enter a Lot/SN.'))
            if self.component_tracking == 'none' and self.qty_done <= 0:
                raise UserError(_('Please enter a positive quantity.'))

            self._update_active_move_line()

            self._create_subsequent_checks()

        if self.test_type == 'picture' and not self.picture:
            raise UserError(_('Please upload a picture.'))

        self.current_quality_check_id.write({
            'quality_state': state,
            'user_id': self.env.user.id,
            'control_date': datetime.now()})
        if self.skip_completed_checks:
            self._change_quality_check(increment=1, children=1, checks=self.skipped_check_ids)
        else:
            self._change_quality_check(increment=1, children=1)

    def action_skip(self):
        self.ensure_one()
        if self.qty_producing <= 0 or self.qty_producing > self.qty_remaining:
            raise UserError(_('Please ensure the quantity to produce is nonnegative and does not exceed the remaining quantity.'))
        if self.skip_completed_checks:
            self._change_quality_check(increment=1, children=1, checks=self.skipped_check_ids)
        else:
            self._change_quality_check(increment=1, children=1)

    def action_first_skipped_step(self):
        self.ensure_one()
        self.skip_completed_checks = True
        self._change_quality_check(position=0, children=1, checks=self.skipped_check_ids)

    def action_previous(self):
        self.ensure_one()
        self._change_quality_check(increment=-1, children=1)

    # Technical function to change the current quality check.
    #
    # params:
    #     children - boolean - Whether to account for 'children' quality checks, which are generated on-the-fly
    #     position - integer - Goes to step <position>, after reordering
    #     checks - list - If provided, consider only checks in <checks>
    #     goto - integer - Goes to quality_check with id=<goto>
    #     increment - integer - Change quality check relatively to the current one, after reordering
    def _change_quality_check(self, **params):
        self.ensure_one()
        check_id = None
        # Determine the list of checks to consider
        checks = params['checks'] if 'checks' in params else self.check_ids
        if not params.get('children'):
            checks = checks.filtered(lambda c: not c.parent_id)
        # We need to make sure the current quality check is in our list
        # when we compute position relatively to the current quality check.
        if 'increment' in params or 'checks' in params and self.current_quality_check_id not in checks:
            checks |= self.current_quality_check_id
        # Restrict to checks associated with the current production
        checks = checks.filtered(lambda c: c.finished_product_sequence == self.qty_produced)
        # As some checks are generated on the fly,
        # we need to ensure that all 'children' steps are grouped together.
        # Missing steps are added at the end.
        def sort_quality_checks(check):
            # Useful tuples to compute the order
            parent_point_sequence = (check.parent_id.point_id.sequence, check.parent_id.point_id.id)
            point_sequence = (check.point_id.sequence, check.point_id.id)
            # Parent quality checks are sorted according to the sequence number of their associated quality point,
            # with chronological order being the tie-breaker.
            if check.point_id and not check.parent_id:
                score = (0, 0) + point_sequence + (0, 0)
            # Children steps follow their parents, honouring their quality point sequence number,
            # with chronological order being the tie-breaker.
            elif check.point_id:
                score = (0, 0) + parent_point_sequence + point_sequence
            # Checks without points go at the end and are ordered chronologically
            elif not check.parent_id:
                score = (check.id, 0, 0, 0, 0, 0)
            # Children without points follow their respective parents, in chronological order
            else:
                score = (check.parent_id.id, check.id, 0, 0, 0, 0)
            return score
        ordered_check_ids = checks.sorted(key=sort_quality_checks).ids
        # We manually add a final 'Summary' step
        # which is not associated with a specific quality_check (hence the 'False' id).
        ordered_check_ids.append(False)
        # Determine the quality check we are switching to
        if 'increment' in params:
            current_id = self.current_quality_check_id.id
            position = ordered_check_ids.index(current_id)
            check_id = self.current_quality_check_id.id
            if position + params['increment'] in range(0, len(ordered_check_ids)):
                position += params['increment']
                check_id = ordered_check_ids[position]
        elif params.get('position') in range(0, len(ordered_check_ids)):
            position = params['position']
            check_id = ordered_check_ids[position]
        elif params.get('goto') in ordered_check_ids:
            check_id = params['goto']
            position = ordered_check_ids.index(check_id)
        # Change the quality check and the worksheet page if necessary
        if check_id is not None:
            next_check = self.env['quality.check'].browse(check_id)
            change_worksheet_page = position != len(ordered_check_ids) - 1 and next_check.point_id.worksheet == 'scroll'
            old_allow_producing_quantity_change = self.allow_producing_quantity_change
            self.write({
                'allow_producing_quantity_change': True if params.get('position') == 0 else False,
                'current_quality_check_id': check_id,
                'is_first_step': position == 0,
                'is_last_step': check_id == False,
                'worksheet_page': next_check.point_id.worksheet_page if change_worksheet_page else self.worksheet_page,
            })
            # Update the default quantities in component registration steps
            if old_allow_producing_quantity_change and not self.allow_producing_quantity_change:
                for check in self.check_ids.filtered(lambda c: c.test_type == 'register_consumed_materials' and c.point_id and c.point_id.component_id.tracking != 'serial' and c.quality_state == 'none'):
                    moves = self.move_raw_ids.filtered(lambda m: m.state not in ('done', 'cancel') and m.product_id == check.point_id.component_id)
                    check.qty_done = float_round(check.qty_done * self.qty_producing, precision_rounding=moves[:1].product_uom.rounding)

    def action_menu(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.workorder',
            'views': [[self.env.ref('mfg_wo.mrp_workorder_view_form_tablet_menu').id, 'form']],
            'name': _('Menu'),
            'target': 'new',
            'res_id': self.id,
        }

    def _compute_check(self):
        for workorder in self:
            todo = False
            fail = False
            for check in workorder.check_ids:
                if check.quality_state == 'none':
                    todo = True
                elif check.quality_state == 'fail':
                    fail = True
                if fail and todo:
                    break
            workorder.quality_check_fail = fail
            workorder.quality_check_todo = todo

    def _compute_quality_alert_count(self):
        for workorder in self:
            workorder.quality_alert_count = len(workorder.quality_alert_ids)

    def _create_checks(self):
        for wo in self:
            # Track components which have a control point
            component_list = []

            production = wo.production_id
            points = self.env['quality.point'].search([('operation_id', '=', wo.operation_id.id),
                                                       ('picking_type_id', '=', production.picking_type_id.id),
                                                       '|', ('product_id', '=', production.product_id.id),
                                                       '&', ('product_id', '=', False), ('product_tmpl_id', '=', production.product_id.product_tmpl_id.id)])
            for point in points:
                # Check if we need a quality control for this point
                if point.check_execute_now():
                    if point.component_id:
                        component_list.append(point.component_id.id)
                    moves = wo.move_raw_ids.filtered(lambda m: m.state not in ('done', 'cancel') and m.product_id == point.component_id and m.workorder_id == wo)
                    qty_done = 1.0
                    if point.component_id and moves and point.component_id.tracking != 'serial':
                        qty_done = float_round(sum(moves.mapped('unit_factor')), precision_rounding=moves[:1].product_uom.rounding)
                    # Do not generate qc for control point of type register_consumed_materials if the component is not consummed in this wo.
                    if not point.component_id or moves:
                        self.env['quality.check'].create({'workorder_id': wo.id,
                                                          'point_id': point.id,
                                                          'team_id': point.team_id.id,
                                                          'product_id': production.product_id.id,
                                                          # Fill in the full quantity by default
                                                          'qty_done': qty_done,
                                                          # Two steps are from the same production
                                                          # if and only if the produced quantities at the time they were created are equal.
                                                          'finished_product_sequence': wo.qty_produced,
                                                          })

            # Generate quality checks associated with unreferenced components
            move_raw_ids = production.move_raw_ids.filtered(lambda m: m.operation_id == wo.operation_id)
            # If last step, add move lines not associated with any operation
            if not wo.next_work_order_id:
                move_raw_ids += production.move_raw_ids.filtered(lambda m: not m.operation_id)
            components = move_raw_ids.mapped('product_id').filtered(lambda product: product.tracking != 'none' and product.id not in component_list)
            quality_team_id = self.env['quality.alert.team'].search([], limit=1).id
            for component in components:
                moves = wo.move_raw_ids.filtered(lambda m: m.state not in ('done', 'cancel') and m.product_id == component)
                qty_done = 1.0
                if component.tracking != 'serial':
                    qty_done = float_round(sum(moves.mapped('unit_factor')) * wo.qty_producing, precision_rounding=moves[:1].product_uom.rounding)
                self.env['quality.check'].create({
                    'workorder_id': wo.id,
                    'product_id': production.product_id.id,
                    'component_id': component.id,
                    'team_id': quality_team_id,
                    # Fill in the full quantity by default
                    'qty_done': float_round(sum(moves.mapped('unit_factor')) * wo.qty_producing, precision_rounding=moves[:1].product_uom.rounding) if component.tracking != 'serial' else 1.0,
                    # Two steps are from the same production
                    # if and only if the produced quantities at the time they were created are equal.
                    'finished_product_sequence': wo.qty_produced,
                })

            # If last step add all the by_product since they are not consumed by a specific operation.
            if not wo.next_work_order_id:
                finished_moves = production.move_finished_ids.filtered(lambda m: not m.workorder_id)
                tracked_by_products = finished_moves.mapped('product_id').filtered(lambda product: product.tracking != 'none' and product != production.product_id)
                for by_product in tracked_by_products:
                    moves = finished_moves.filtered(lambda m: m.state not in ('done', 'cancel') and m.product_id == by_product)
                    if by_product.tracking == 'serial':
                        qty_done = 1.0
                    else:
                        qty_done = float_round(sum(moves.mapped('unit_factor')) * wo.qty_producing, precision_rounding=moves[:1].product_uom.rounding)
                    self.env['quality.check'].create({
                        'workorder_id': wo.id,
                        'product_id': production.product_id.id,
                        'component_id': by_product.id,
                        'team_id': quality_team_id,
                        # Fill in the full quantity by default
                        'qty_done': qty_done,
                        'component_is_byproduct': True,
                        # Two steps are from the same production
                        # if and only if the produced quantities at the time they were created are equal.
                        'finished_product_sequence': wo.qty_produced,
                    })

            # Set default quality_check
            wo.skip_completed_checks = False
            wo._change_quality_check(position=0)

    def _get_byproduct_move_to_update(self):
        moves = super(MrpProductionWorkcenterLine, self)._get_byproduct_move_to_update()
        return moves.filtered(lambda m: m.product_id.tracking == 'none')

    def record_production(self):
        self.ensure_one()
        if any([(x.quality_state == 'none') for x in self.check_ids]):
            raise UserError(_('You still need to do the quality checks!'))
        if (self.production_id.product_id.tracking != 'none') and not self.final_lot_id and self.move_raw_ids:
            raise UserError(_('You should provide a lot for the final product'))
        if self.check_ids:
            # Check if you can attribute the lot to the checks
            if (self.production_id.product_id.tracking != 'none') and self.final_lot_id:
                checks_to_assign = self.check_ids.filtered(lambda x: not x.lot_id)
                if checks_to_assign:
                    checks_to_assign.write({'lot_id': self.final_lot_id.id})
        res = super(MrpProductionWorkcenterLine, self).record_production()
        if self.qty_producing > 0:
            self._create_checks()
        return res

    # --------------------------
    # Buttons from quality.check
    # --------------------------

    def open_tablet_view(self):
        self.ensure_one()
        if not self.is_user_working and self.working_state != 'blocked':
            self.button_start()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.workorder',
            'views': [[self.env.ref('mfg_wo.mrp_workorder_view_form_tablet').id, 'form']],
            'res_id': self.id,
            'target': 'fullscreen',
            'flags': {
                'headless': True,
                'form_view_initial_mode': 'edit',
            },
        }

    def action_next(self):
        self.ensure_one()
        return self._next()

    def action_open_manufacturing_order(self):
        action = self.do_finish()
        try:
            self.production_id.button_mark_done()
        except (UserError, ValidationError) as e:
            # log next activity on MO with error message
            self.env['mail.activity'].create({
                'res_id': self.production_id.id,
                'res_model_id': self.env['ir.model']._get(self.production_id._name).id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_warning').id,
                'summary': ('The %s could not be closed') % (self.production_id.name),
                'note': e.name,
                'user_id': self.env.user.id,
            })
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'mrp.production',
                'views': [[self.env.ref('mrp.mrp_production_form_view').id, 'form']],
                'res_id': self.production_id.id,
                'target': 'main',
                'flags': {
                    'headless': False,
                },
            }
        return action

    def do_finish(self):
        self.record_production()
        action = self.env.ref('mfg_wo.mrp_workorder_action_tablet').read()[0]
        action['domain'] = [('state', 'not in', ['done', 'cancel', 'pending']), ('workcenter_id', '=', self.workcenter_id.id)]
        return action

    def on_barcode_scanned(self, barcode):
        # qty_done field for serial numbers is fixed
        if self.component_tracking != 'serial':
            if not self.lot_id:
                # not scanned yet
                self.qty_done = 1
            elif self.lot_id.name == barcode:
                self.qty_done += 1
            else:
                return {
                    'warning': {
                        'title': _("Warning"),
                        'message': _("You are using components from another lot. \nPlease validate the components from the first lot before using another lot.")
                    }
                }

        lot = self.env['stock.production.lot'].search([('name', '=', barcode)])

        if self.component_tracking:
            if not lot:
                # create a new lot
                # create in an onchange is necessary here ("new" cannot work here)
                lot = self.env['stock.production.lot'].create({
                    'name': barcode,
                    'product_id': self.component_id.id,
                })
            self.lot_id = lot
        elif self.production_id.product_id.tracking and self.production_id.product_id.tracking != 'none':
            if not lot:
                lot = self.env['stock.production.lot'].create({
                    'name': barcode,
                    'product_id': self.product_id.id,
                })
            self.final_lot_id = lot