odoo.define('mfg_stockbar.PickingBarcodeHandler', function (require) {
"use strict";

var core = require('web.core');
var AbstractField = require('web.AbstractField');
var field_registry = require('web.field_registry');
var FormController = require('web.FormController');

var _t = core._t;

FormController.include({
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Override to take into account 'location_processed' and 'result_package_id'
     * to determine whether or not the given barcode matches the given record in
     * the case of a 'picking_barcode_handler' widget.
     *
     * @private
     * @override
     * @param {Object} record
     * @param {string} barcode
     * @param {Object} activeBarcode
     * @returns {boolean}
     */
    _barcodeRecordFilter: function (record, barcode, activeBarcode) {
        var matching = this._super.apply(this, arguments);
        if (activeBarcode.widget === 'picking_barcode_handler') {
            var data = record.data;
            matching = matching && !data.location_processed && !data.result_package_id;
        }
        return matching;
    },
    /**
     * Method called when a record is already found
     *
     * @private
     * @override
     * @param {Object} candidate (already exists in the x2m)
     * @param {Object} record
     * @param {string} barcode
     * @param {Object} activeBarcode
     * @returns {Deferred}
     */
    _barcodeSelectedCandidate: function (candidate, record, barcode, activeBarcode) {
        if (activeBarcode.widget === 'picking_barcode_handler' && candidate.data.lots_visible) {
            var self = this;
            // the product is tracked by lot -> open the split lot wizard
            // save the record for the server to be aware of the operation
            return this.saveRecord(this.handle, {stayInEdit: true, reload: false}).then(function () {
                return self._rpc({
                    model: 'stock.picking',
                    method: 'get_po_to_split_from_barcode',
                    args: [[record.data.id], barcode],
                }).done(function (action) {
                    // the function returns an action (wizard)
                    self._barcodeStopListening();
                    self.do_action(action, {
                        on_close: function() {
                            self._barcodeStartListening();
                            self.update({}, {reload: true});
                        }
                    });
                });
            });
        }
        return this._super.apply(this, arguments);
    },
    /**
     *
     * @see _barcodeAddX2MQuantity
     *
     * @private
     * @param {string} barcode
     * @param {Object} activeBarcode
     * @returns {Deferred}
     */
    _barcodePickingAddRecordId: function (barcode, activeBarcode) {
        if (!activeBarcode.handle) {
            return $.Deferred().reject();
        }
        var record = this.model.get(activeBarcode.handle);
        if (record.data.state === 'cancel' || record.data.state === 'done') {
            this.do_warn(_.str.sprintf(_t("Picking %s"), record.data.state),
                _.str.sprintf(_t("The picking is %s and cannot be edited."), record.data.state));
            return $.Deferred().reject();
        }
        return this._barcodeAddX2MQuantity(barcode, activeBarcode);
    }
});


var PickingBarcodeHandler = AbstractField.extend({
    init: function() {
        this._super.apply(this, arguments);

        this.trigger_up('activeBarcode', {
            name: this.name,
            notifyChange: false,
            fieldName: 'move_line_ids_without_package',
            quantity: 'qty_done',
            setQuantityWithKeypress: true,
            commands: {
                'barcode': '_barcodePickingAddRecordId',
                'O-CMD.MAIN-MENU': _.bind(this.do_action, this, 'mfg_stockbar.stock_barcode_action_main_menu', {clear_breadcrumbs: true}),
            }
        });
    },
});

field_registry.add('picking_barcode_handler', PickingBarcodeHandler);

return PickingBarcodeHandler;

});
