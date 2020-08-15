odoo.define('mfg_wo.update_kanban', function (require) {
"use strict";

var basic_fields = require('web.basic_fields');
var field_registry = require('web.field_registry');
var KanbanController = require('web.KanbanController');
var KanbanRecord = require('web.KanbanRecord');
var KanbanView = require('web.KanbanView');
var view_registry = require('web.view_registry');
var ListController = require('web.ListController');
var ListView = require('web.ListView');

var FieldInteger = basic_fields.FieldInteger;
var FieldBinaryImage = basic_fields.FieldBinaryImage;

var core = require('web.core');
var QWeb = core.qweb;

KanbanRecord.include({
    _openRecord: function () {
        if (this.modelName === 'mrp.workorder') {
            var self = this;
            this._rpc({
                method: 'open_tablet_view',
                model: self.modelName,
                args: [self.id],
            }).then(function (result) {
                self.do_action(result);
            });
        } else {
            this._super.apply(this, arguments);
        }
    },
});

var BackArrow = FieldInteger.extend({
    events: {
        'click': '_onClick',
    },
    _render: function () {
        this.$el.html('<button class="btn btn-secondary o_workorder_icon_btn o_workorder_icon_back"><i class="fa fa-arrow-left"/></button>');
    },
    _onClick: function () {
        var self = this;
        this._rpc({
            method: 'action_back',
            model: 'mrp.workorder',
            args: [self.recordData.id],
        }).then(function () {
            self.do_action('mfg_wo.mrp_workorder_action_tablet', {
                additional_context: {active_id: self.record.data.workcenter_id.res_id},
                clear_breadcrumbs: true,
            });
        });
    },
});

var TabletImage = FieldBinaryImage.extend({
    template: 'FieldBinaryTabletImage',
    events: _.extend({}, FieldBinaryImage.prototype.events, {
        'click .o_form_image_controls': '_onOpenPreview',
        'click .o_input_file': function (ev) {
            ev.stopImmediatePropagation();
        },
    }),

    /**
     * After render, hide the controls if no image is set
     *
     * @return {Deferred}
     * @override
     * @private
     */
    _render: function (){
        var def = this._super.apply(this, arguments);
        this.$('.o_form_image_controls').toggleClass('o_invisible_modifier', !this.value);
        return def;
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Just prevent propagation of click event on the overlay
     * that opens the preview when the Trash button is clicked
     *
     * @override
     */
    _onClearClick: function (ev){
        ev.stopImmediatePropagation();
        this._super.apply(this, arguments);
    },

    /**
     * Open the image preview
     *
     * @private
     */
    _onOpenPreview: function (ev) {
        ev.stopPropagation();
        this.src = this.$el.find('>img').attr('src');

        this.$modal = $(QWeb.render('FieldBinaryTabletImage.Preview', {
            url: this.src
        }));
        this.$modal.click(this._onClosePreview.bind(this));
        this.$modal.appendTo('body');
        this.$modal.modal('show');
    },

    /**
     * Close the image preview
     *
     * @private
     */
    _onClosePreview: function (ev) {
        ev.preventDefault();
        this.$modal.remove();
        $('.modal-backdrop').remove();
    },
});

function tabletRenderButtons($node) {
        var self = this;
        this.$buttons = $('<div/>');
        this.$buttons.html('<button class="btn btn-secondary back-button"><i class="fa fa-arrow-left"/></button>');
        this.$buttons.on('click', function () {
            self.do_action('mrp.mrp_workcenter_kanban_action', {clear_breadcrumbs: true});
        });
        this.$buttons.appendTo($node);
}

var TabletKanbanController = KanbanController.extend({
    renderButtons: function ($node) {
        return tabletRenderButtons.apply(this, arguments);
    },
});

var TabletKanbanView = KanbanView.extend({
    config: _.extend({}, KanbanView.prototype.config, {
        Controller: TabletKanbanController,
    }),
});

var TabletListController = ListController.extend({
    renderButtons: function ($node) {
        return tabletRenderButtons.apply(this, arguments);
    },
});

var TabletListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: TabletListController,
    }),
});

field_registry.add('back_arrow', BackArrow);
field_registry.add('tablet_image', TabletImage);
view_registry.add('tablet_kanban_view', TabletKanbanView);
view_registry.add('tablet_list_view', TabletListView);

return {
    BackArrow: BackArrow,
    TabletImage: TabletImage,
    TabletKanbanView: TabletKanbanView,
    TabletListView: TabletListView,
};
});
