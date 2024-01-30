odoo.define('document.documentListView', function (require) {
"use strict";

/**
 * This file defines the documentListView, a JS extension of the ListView to
 * deal with document.
 *
 * Warning: there is no groupby menu in this view as it doesn't support the
 * grouped case. Its elements assume that the data isn't grouped.
 */

const documentListController = require('document.documentListController');
const documentListModel = require('document.documentListModel');
const documentListRenderer = require('document.documentListRenderer');
const documentSearchPanel = require('document.documentSearchPanel');
const documentView = require('document.viewMixin');

const ListView = require('web.ListView');
const viewRegistry = require('web.view_registry');

const documentListView = ListView.extend(documentView, {
    config: Object.assign({}, ListView.prototype.config, {
        Controller: documentListController,
        Model: documentListModel,
        Renderer: documentListRenderer,
        SearchPanel: documentSearchPanel,
    }),
    searchMenuTypes: ['filter', 'favorite'],
});

viewRegistry.add('document_list', documentListView);

return documentListView;

});
