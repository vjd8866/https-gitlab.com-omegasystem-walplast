odoo.define('document.documentKanbanView', function (require) {
'use strict';

/**
 * This file defines the documentKanbanView, a JS extension of the KanbanView
 * to deal with document.
 *
 * Warning: there is no groupby menu in this view as it doesn't support the
 * grouped case. Its elements assume that the data isn't grouped.
 */

const documentKanbanController = require('document.documentKanbanController');
const documentKanbanModel = require('document.documentKanbanModel');
const documentKanbanRenderer = require('document.documentKanbanRenderer');
const documentSearchPanel = require('document.documentSearchPanel');
const documentViewMixin = require('document.viewMixin');

const KanbanView = require('web.KanbanView');
const viewRegistry = require('web.view_registry');

const { _lt } = require('web.core');

const documentKanbanView = KanbanView.extend(documentViewMixin, {
    config: Object.assign({}, KanbanView.prototype.config, {
        Controller: documentKanbanController,
        Model: documentKanbanModel,
        Renderer: documentKanbanRenderer,
        SearchPanel: documentSearchPanel,
    }),
    display_name: _lt('Attachments Kanban'),
    searchMenuTypes: ['filter', 'favorite'],
});

viewRegistry.add('document_kanban', documentKanbanView);

return documentKanbanView;

});
