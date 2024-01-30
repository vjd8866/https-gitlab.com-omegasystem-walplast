odoo.define('document.documentKanbanRenderer', function (require) {
'use strict';

/**
 * This file defines the Renderer for the document Kanban view, which is an
 * override of the KanbanRenderer.
 */

const documentKanbanRecord = require('document.documentKanbanRecord');

const KanbanRenderer = require('web.KanbanRenderer');

const documentKanbanRenderer = KanbanRenderer.extend({
    config: Object.assign({}, KanbanRenderer.prototype.config, {
        KanbanRecord: documentKanbanRecord,
    }),

    /**
     * @override
     */
    async start() {
        this.$el.addClass('o_document_kanban_view o_document_view position-relative align-content-start flex-grow-1 flex-shrink-1');
        await this._super(...arguments);
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Marks records as selected
     *
     * @private
     * @param {integer[]} selectedRecordIds
     */
    updateSelection(selectedRecordIds) {
        for (const widget of this.widgets) {
            const isSelected = selectedRecordIds.includes(widget.getResId());
            widget.updateSelection(isSelected);
        }
    },
});

return documentKanbanRenderer;

});
