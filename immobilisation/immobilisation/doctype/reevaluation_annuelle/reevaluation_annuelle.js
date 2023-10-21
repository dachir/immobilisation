// Copyright (c) 2023, Richard Amouzou and contributors
// For license information, please see license.txt

frappe.ui.form.on('Reevaluation Annuelle', {
	refresh: function(frm) {
		frm.set_query('ratio',() => {
			return {
				filters: {
					"docstatus": 1,
				}
			};
		});
		frm.set_query('asset', 'asset_details', () => {
			return {
				filters: {
					"status": ["IN", ["Submitted","Partially Depreciated"]],
					"docstatus": 1,
				}
			};
		});
		frm.add_custom_button(
			__("Liste des Immos"),
			function () {
				frm.call("get_assets");
			}, "Utilitaires"
		);
	},
});
