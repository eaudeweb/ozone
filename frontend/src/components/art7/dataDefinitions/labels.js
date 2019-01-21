import { getCommonLabels } from '@/components/common/dataDefinitions/labels'

const getLabels = ($gettext) => {
	const labels = {
		common: getCommonLabels($gettext),
		has_imports: {
			substance: $gettext('Substances'),
			blend: $gettext('Blend'),
			group: $gettext('Group'),
			percent: $gettext('Percentage'),
			source_party: $gettext('Exporting party for quantities reported as imports'),
			quantity_total_new: $gettext('Total quantity imported for all uses (new)'),
			quantity_total_recovered: $gettext('Total quantity imported for all uses (recovered and reclaimed)'),
			quantity_feedstock: $gettext('Quantity of new substances imported as feedstock'),
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
			quantity_other_uses: $gettext('Other/unspecified'),
			decision_other_uses: $gettext('Other/unspecified'),
			quantity_polyols: $gettext('Polyols'),
			decision_polyols: $gettext('Polyols'),
			decision: $gettext('Decision'),
			quantity: $gettext('Quantity'),
			remarks_os: $gettext('Remarks (Secretariat)'),
			remarks_party: $gettext('Remarks (Party)'),
			imports_remarks_secretariat: $gettext('Comments (Secretariat)'),
			imports_remarks_party: $gettext('Comments (Party)')
		},
		has_exports: {
			substance: $gettext('Substances'),
			blend: $gettext('Blend'),
			percent: $gettext('Percentage'),
			group: $gettext('Group'),
			quantity_polyols: $gettext('Polyols'),
			decision_polyols: $gettext('Polyols'),
			destination_party: $gettext('Country of destination of exports'),
			quantity_total_new: $gettext('Total quantity imported for all uses (new)'),
			quantity_total_recovered: $gettext('Total quantity imported for all uses (recovered and reclaimed)'),
			quantity_feedstock: $gettext('Quantity of new substances imported as feedstock'),
			quantity_exempted: $gettext('Quantity of new substance exported for exempted essential, critical, high-ambient-temperature or other uses'),
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
			quantity_other_uses: $gettext('Other/unspecified'),
			decision_other_uses: $gettext('Other/unspecified'),
			decision: $gettext('Decision'),
			quantity: $gettext('Quantity'),
			remarks_os: $gettext('Remarks (Secretariat)'),
			remarks_party: $gettext('Remarks (Party)'),
			exports_remarks_party: $gettext('Comments (Party)'),
			exports_remarks_secretariat: $gettext('Comments (Secretariat)')
		},
		has_produced: {
			remarks_party: $gettext('Remarks (Party)'),
			remarks_os: $gettext('Remarks (Secretariat)'),
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
			quantity_other_uses: $gettext('Other/unspecified'),
			decision_other_uses: $gettext('Other/unspecified'),
			quantity_total_produced: $gettext('Total production for all uses'),
			quantity_feedstock: $gettext('Production for feedstock uses within your country'),
			quantity_article_5: $gettext('Production for supply to article 5 countries in accordance with articles 2a 2h and 5'),
			substance: $gettext('Substances'),
			quantity_exempted: $gettext('Production for exempted essential, critical or other uses within your country'),
			decision: $gettext('Decision'),
			quantity: $gettext('Quantity'),
			production_remarks_party: $gettext('Comments (Party)'),
			production_remarks_secretariat: $gettext('Comments (Secretariat)')
		},
		has_destroyed: {
			remarks_party: $gettext('Remarks (Party)'),
			remarks_os: $gettext('Remarks (Secretariat)'),
			percent: $gettext('Percentage'),
			quantity_destroyed: $gettext('Quantity destroyed'),
			substance: $gettext('Substances'),
			blend: $gettext('Blend'),
			destruction_remarks_party: $gettext('Comments (Party)'),
			destruction_remarks_secretariat: $gettext('Comments (Secretariat)')
		},
		has_nonparty: {
			remarks_party: $gettext('Remarks (Party)'),
			remarks_os: $gettext('Remarks (Secretariat)'),
			percent: $gettext('Percentage'),
			quantity_import_new: $gettext('Quantity of imports from non-parties (new)'),
			quantity_import_recovered: $gettext('Quantity of imports from non-parties (recovered)'),
			quantity_export_new: $gettext('Quantity of exports to non-parties (new)'),
			quantity_export_recovered: $gettext('Quantity of exports to non-parties (recovered)'),
			substance: $gettext('Substance'),
			blend: $gettext('Blend'),
			trade_party: $gettext('Exporting party for quantities reported as imports or country of destination of exports'),
			nonparty_remarks_party: $gettext('Comments (Party)'),
			nonparty_remarks_secretariat: $gettext('Comments (Secretariat)')
		},
		has_emissions: {
			facility_name: $gettext('Facility name or identifier'),
			quantity_generated: $gettext('Amount [generated] (tonnes)'),
			quantity_feedstock: $gettext('Amount used for feedstock'),
			quantity_destroyed: $gettext('Amount destroyed'),
			quantity_emitted: $gettext('Amount of emissions'),
			remarks_party: $gettext('Remarks (Party)'),
			remarks_os: $gettext('Remarks (Secretariat)'),
			emissions_remarks_party: $gettext('Comments (Party)'),
			emissions_remarks_secretariat: $gettext('Comments (Secretariat)')
		}
	}

	return labels
}

export {
	getLabels
}
