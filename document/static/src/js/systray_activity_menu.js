odoo.define('document.systray.ActivityMenu', function (require) {
"use strict";

var ActivityMenu = require('mail.systray.ActivityMenu');

const session = require('web.session');

ActivityMenu.include({
    events: _.extend({}, ActivityMenu.prototype.events, {
        'click .o_sys_document_request': '_onRequestDocument',
    }),

    /**
     * @override
     */
    async willStart() {
        await this._super(...arguments);
        this.hasDocumentUserGroup = await session.user_has_group('document.group_document_user');
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {MouseEvent} ev
     */
   _onRequestDocument: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this.$('.dropdown-toggle').dropdown('toggle');
        this.do_action('document.action_request_form');
    },
});
});
