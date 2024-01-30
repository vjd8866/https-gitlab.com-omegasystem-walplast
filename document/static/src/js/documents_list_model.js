odoo.define('document.documentListModel', function (require) {
'use strict';

/**
 * This file defines the Model for the document List view, which is an
 * override of the ListModel.
 */
const ListModel = require('web.ListModel');
const documentModelMixin = require('document.modelMixin');

const documentListModel = ListModel.extend(documentModelMixin);

return documentListModel;

});
