const getLabels = ($gettext) => {
	const labels = {
		has_imports: {
			substance: $gettext('Substances'),
			blend: $gettext('Blend'),
			group: $gettext('Group'),
			percent: $gettext('Percentage'),
			source_party: $gettext('Exporting party for quantities reported as imports'),
			quantity_total_new: $gettext('Total Quantity Imported for All Uses (new)'),
			quantity_total_recovered: $gettext('Total Quantity Imported for All Uses (recovered and reclaimed)'),
			quantity_feedstock: $gettext('Quantity of New Substances Imported as Feedstock'),
			quantity_exempted: $gettext('Quantity of new substance imported for exempted essential, critical, high-ambient-temperature or other uses'),
			quantity_essential_uses: $gettext('Essential use, other than L&A'),
			decision_essential_uses: $gettext('Essential use, other than L&A'),
			quantity_critical_uses: $gettext('Critical use'),
			decision_critical_uses: $gettext('Critical use'),
			quantity_high_ambient_temperature: $gettext('High ambient temperature'),
			decision_high_ambient_temperature: $gettext('High ambient temperature'),
			quantity_process_agent_uses: $gettext('Process agent uses'),
			decision_process_agent_uses: $gettext('Process agent uses'),
			quantity_laboratory_analytical_uses: $gettext('Laboratory and analytical'),
			decision_laboratory_analytical_uses: $gettext('Laboratory and analytical'),
			quantity_quarantine_pre_shipment: $gettext('Quarantine and pre-shipment applications'),
			decision_quarantine_pre_shipment: $gettext('Quarantine and pre-shipment applications'),
			quantity_other_uses: $gettext('Other/Unspecified'),
			decision_other_uses: $gettext('Other/Unspecified'),
			decision: $gettext('Decision'),
			quantity: $gettext('Quantity'),
			remarks_os: $gettext('Remarks (Secretariat)'),
			remarks_party: $gettext('Remarks (Party)')
		},
		has_exports: {
			substance: $gettext('Substances'),
			blend: $gettext('Blend'),
			percent: $gettext('Percentage'),
			group: $gettext('Group'),
			destination_party: $gettext('Country of Destination of Exports'),
			quantity_total_new: $gettext('Total Quantity Imported for All Uses (new)'),
			quantity_total_recovered: $gettext('Total Quantity Imported for All Uses (recovered and reclaimed)'),
			quantity_feedstock: $gettext('Quantity of New Substances Imported as Feedstock'),
			quantity_exempted: $gettext('Quantity of new substance Exported for exempted essential, critical, high-ambient-temperature or other uses'),
			decision_exempted: $gettext('Decision'),
			quantity_essential_uses: $gettext('Essential use, other than L&A'),
			decision_essential_uses: $gettext('Essential use, other than L&A'),
			quantity_critical_uses: $gettext('Critical use'),
			decision_critical_uses: $gettext('Critical use'),
			quantity_high_ambient_temperature: $gettext('High ambient temperature'),
			decision_high_ambient_temperature: $gettext('High ambient temperature'),
			quantity_process_agent_uses: $gettext('Process agent uses'),
			decision_process_agent_uses: $gettext('Process agent uses'),
			quantity_laboratory_analytical_uses: $gettext('Laboratory and analytical'),
			decision_laboratory_analytical_uses: $gettext('Laboratory and analytical'),
			quantity_quarantine_pre_shipment: $gettext('Quarantine and pre-shipment applications'),
			decision_quarantine_pre_shipment: $gettext('Quarantine and pre-shipment applications'),
			quantity_other_uses: $gettext('Other/Unspecified'),
			decision_other_uses: $gettext('Other/Unspecified'),
			decision: $gettext('Decision'),
			quantity: $gettext('Quantity'),
			remarks_os: $gettext('Remarks (Secretariat)'),
			remarks_party: $gettext('Remarks (Party)')
		},
		has_produced: {
			remarks_party: $gettext('Remarks (Secretariat)'),
			remarks_os: $gettext('Remarks (Party)'),
			percent: $gettext('Percentage'),
			quantity_critical_uses: $gettext('Critical use'),
			decision_critical_uses: $gettext('Critical use'),
			quantity_essential_uses: $gettext('Essential use, other than L&A'),
			decision_essential_uses: $gettext('Essential use, other than L&A'),
			quantity_high_ambient_temperature: $gettext('High ambient temperature'),
			decision_high_ambient_temperature: $gettext('High ambient temperature'),
			quantity_process_agent_uses: $gettext('Process agent uses'),
			decision_process_agent_uses: $gettext('Process agent uses'),
			quantity_laboratory_analytical_uses: $gettext('Laboratory and analytical'),
			decision_laboratory_analytical_uses: $gettext('Laboratory and analytical'),
			quantity_quarantine_pre_shipment: $gettext('Quarantine and pre-shipment applications'),
			decision_quarantine_pre_shipment: $gettext('Quarantine and pre-shipment applications'),
			quantity_other_uses: $gettext('Other/Unspecified'),
			decision_other_uses: $gettext('Other/Unspecified'),
			quantity_total_produced: $gettext('Total production for all uses'),
			quantity_feedstock: $gettext('Production for feedstock uses within your country'),
			quantity_article_5: $gettext('Production for supply to Article 5 countries in accordance with Articles 2A 2H and 5'),
			substance: $gettext('Substances'),
			quantity_exempted: $gettext('Production for exempted essential, critical or other uses within your country'),
			decision: $gettext('Decision'),
			quantity: $gettext('Quantity')
		},
		has_destroyed: {
			remarks_party: $gettext('Remarks (Secretariat)'),
			remarks_os: $gettext('Remarks (Party)'),
			percent: $gettext('Percentage'),
			quantity_destroyed: $gettext('Quantity destroyed'),
			substance: $gettext('Substances'),
			blend: $gettext('blend')
		},
		has_nonparty: {
			remarks_party: $gettext('Remarks (Secretariat)'),
			remarks_os: $gettext('Remarks (Party)'),
			percent: $gettext('Percentage'),
			quantity_import_new: $gettext('Quantity of imports from non-parties (new)'),
			quantity_import_recovered: $gettext('Quantity of imports from non-parties (recovered)'),
			quantity_export_new: $gettext('Quantity of exports to non-parties (new)'),
			quantity_export_recovered: $gettext('Quantity of exports to non-parties (recovered)'),
			substance: $gettext('Substance'),
			blend: $gettext('Blend'),
			trade_party: $gettext('Exporting party for quantities reported as imports OR Country of destination of exports')
		},
		has_emissions: {
			facility_name: $gettext('Facility name or identifier'),
			quantity_generated: $gettext('Amount [Generated] (tonnes)'),
			quantity_feedstock: $gettext('Amount Used for Feedstock'),
			quantity_destroyed: $gettext('Amount Destroyed'),
			quantity_emitted: $gettext('Amount of Emissions'),
			remarks_party: $gettext('Remarks (Secretariat)'),
			remarks_os: $gettext('Remarks (Party)')
		},
		general: {
			__all__: '',
			recall: $gettext('Recall'),
			process: $gettext('Process'),
			finalize: $gettext('Finalize'),
			submit: $gettext('Submit'),
			unrecall_to_submitted: $gettext('Reinstate'),
			unrecall_to_processing: $gettext('Reinstate'),
			unrecall_to_finalized: $gettext('Reinstate'),
			reporting_officer: $gettext('Name of reporting officer'),
			designation: $gettext('Designation'),
			organization: $gettext('Organization'),
			postal_code: $gettext('Postal Adddress'),
			country: $gettext('Country'),
			phone: $gettext('Phone'),
			fax: $gettext('Fax'),
			email: $gettext('E-mail'),
			date: $gettext('Date')
		}
	}
	return labels
}

export {
	getLabels
}
