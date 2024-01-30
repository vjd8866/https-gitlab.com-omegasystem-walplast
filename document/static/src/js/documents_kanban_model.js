odoo.define('document.documentKanbanModel', function (require) {
"use strict";

/**
 * This file defines the Model for the document Kanban view, which is an
 * override of the KanbanModel.
 */

const documentModelMixin = require('document.modelMixin');

const KanbanModel = require('web.KanbanModel');


const documentKanbanModel = KanbanModel.extend(documentModelMixin);

return documentKanbanModel;

});
