odoo.define('document.documentListController', function (require) {
'use strict';

const documentControllerMixin = require('document.controllerMixin');
const ListController = require('web.ListController');

const { qweb } = require('web.core');

const documentListController = ListController.extend(documentControllerMixin, {
    events: Object.assign({}, ListController.prototype.events, documentControllerMixin.events),
    custom_events: Object.assign({}, ListController.prototype.custom_events, documentControllerMixin.custom_events, {
        document_view_rendered: '_ondocumentViewRendered',
        toggle_all: '_onToggleAll',
    }),

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
        this.$('.o_content').addClass('o_document_content');
        await this._super(...arguments);
        documentControllerMixin.start.apply(this, arguments);
    },

    /**
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

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _ondocumentViewRendered() {
        this.$('.o_data_row').attr('draggable', true).addClass('o_document_draggable o_document_list_record');
        const localData = this.model.localData;
        for (const key in localData) {
            const $record = this.$(`.o_document_list_record[data-id="${key}"]`);
            $record.attr('data-res-id', localData[key].data.id);
            const lockLocalId = localData[key].data.lock_uid;
            if (lockLocalId) {
                const lockUidData = localData[lockLocalId].data;
                $record.find('.o_data_cell:nth(0)').append(qweb.render('document.lockIcon', {
                    tooltip: lockUidData.display_name,
                }));
            }
        }
    },
    /**
     *
     * @private
     * @param {OdooEvent} ev
     */
    async _onToggleAll(ev) {
        const state = this.model.get(this.handle);
        this._selectedRecordIds = ev.data.checked ? state.data.map(record => record.res_id) : [];
        await Promise.all([
            this._updateChatter(state),
            this._renderdocumentInspector(state)
        ]);
        this._updateSelection();
    },

});

return documentListController;

});
