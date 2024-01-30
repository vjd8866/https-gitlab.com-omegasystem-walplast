odoo.define('sales_meet.MastersDashboard', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var rpc = require('web.rpc');
var QWeb = core.qweb;
var _lt = core._lt;
var _t = core._t;

var MastersDashboard = AbstractAction.extend({
    template: "sales_meet.MastersDashboardMain",
    events: {
        'click .go_to_wp_customer':'go_to_wp_customer',
        'click .go_to_supplier':'go_to_supplier',
        'click .go_to_product':'go_to_product',
        'click .partner_count':'partner_count',

    },

     init: function(parent, action) {
           this._super(parent, action);
       },

    start: function() {
        var self = this;
        self._rpc({
                       model: 'calendar.event',
                       method: 'get_user_meeting_details',
                       args: [],
                   }).then(function (data) {
            self.$('.o_masters_dashboard').html(QWeb.render('MastersManagerDashboard', {widget: data}));

        });

    },

    go_to_wp_customer: function(e) {
        var self = this;

        self.do_action({
            type: 'ir.actions.act_window',
            res_model: "wp.res.partner",
            // res_id: id,
            view_mode: 'form',
            views: [[false, 'form']],
            domain: [['customer','=', true]],
            context: {'default_active': true,
                        'default_customer': true,

                    },
        });
    },

    partner_count: function(e) {
        var self = this;

        this.do_action({
            name: _t("Distributors"),
            type: 'ir.actions.act_window',
            res_model: 'wp.res.partner',
            view_mode: 'tree,form',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            target: 'current'
        })
    },


    go_to_supplier: function(e) {
        var self = this;
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: "res.partner",
            // res_id: id,
            views: [[false, 'form']],
            domain: [['supplier_rank','=', 1]],
            context: {'default_supplier_rank': 1,
                        'default_customer_rank': 0,

                    },
        });
    },


    go_to_product: function(e) {
        var self = this;

        this.do_action({
            type: 'ir.actions.act_window',
            res_model: "product.product",
            // res_id: id,
            views: [[false, 'form']],
        });
    },

});
core.action_registry.add('masters_dashboard', MastersDashboard);

return MastersDashboard;

});
