odoo.define('document.documentKanbanController', function (require) {
'use strict';

/**
 * This file defines the Controller for the document Kanban view, which is an
 * override of the KanbanController.
 */

const documentControllerMixin = require('document.controllerMixin');

const KanbanController = require('web.KanbanController');

var documentKanbanController = KanbanController.extend(documentControllerMixin, {
    events: Object.assign({}, KanbanController.prototype.events, documentControllerMixin.events),
    custom_events: Object.assign({}, KanbanController.prototype.custom_events, documentControllerMixin.custom_events),

    /**
     * @override
     */
    init() {
        this._super(...arguments);
        documentControllerMixin.init.apply(this, arguments);
    },
    /**
     * @override
     */
    async start() {
        this.$('.o_content').addClass('o_document_content o_document_kanban');
        await this._super(...arguments);
        documentControllerMixin.start.apply(this, arguments);
    },
    /**
     * Override to update the records selection.
     *
     * @override
     */
    async reload() {
        await this._super(...arguments);
        await documentControllerMixin.reload.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     * @private
     */
    async _update() {
        await this._super(...arguments);
        await documentControllerMixin._update.apply(this, arguments);
    },
    /**
     * @override
     * @private
     */
    updateButtons() {
        this._super(...arguments);
        documentControllerMixin.updateButtons.apply(this, arguments);
    },
});

return documentKanbanController;

});
