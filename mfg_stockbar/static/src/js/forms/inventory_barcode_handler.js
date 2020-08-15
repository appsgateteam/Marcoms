odoo.define('mfg_stockbar.InventoryBarcodeHandler', function (require) {
"use strict";

var field_registry = require('web.field_registry');
var AbstractField = require('web.AbstractField');

var InventoryBarcodeHandler = AbstractField.extend({
    init: function() {
        this._super.apply(this, arguments);

        this.trigger_up('activeBarcode', {
            name: this.name,
            notifyChange: false,
            fieldName: 'line_ids',
            quantity: 'product_qty',
            setQuantityWithKeypress: true,
            commands: {
                'O-CMD.MAIN-MENU': _.bind(this.do_action, this, 'mfg_stockbar.stock_barcode_action_main_menu', {clear_breadcrumbs: true}),
                barcode: '_barcodeAddX2MQuantity',
            }
        });
    },
});

field_registry.add('inventory_barcode_handler', InventoryBarcodeHandler);

});
