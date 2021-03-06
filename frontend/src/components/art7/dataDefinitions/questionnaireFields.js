const getCommonQuestionnaireOptions = ($gettext) => [{ text: $gettext('Yes'), value: true }, { text: $gettext('No'), value: false }]

const getQuestionnaireFields = ($gettext) => {
  const questionnaireFields = {
    has_imports: {
      label: `1. ${$gettext('Did your country import CFCs, halons, carbon tetrachloride, methyl chloroform, HCFCs, HBFCs, bromochloromethane, methyl bromide or HFCs in the reporting year?')}`,
      type: 'questionnaireRadio',
      name: 'has_imports',
      selected: null,
      options: getCommonQuestionnaireOptions($gettext),
      info: $gettext('If No, ignore data form 1 and go to question 2. If Yes, please complete data form 1. Please read Instruction I of the document carefully before filling in the form.')
    },
    has_exports: {
      label: `2. ${$gettext('Did your country export or re-export CFCs, halons, carbon tetrachloride, methyl chloroform, HCFCs, HBFCs, bromochloromethane, methyl bromide or HFCs in the reporting year?')}`,
      type: 'questionnaireRadio',
      name: 'has_exports',
      selected: null,
      options: getCommonQuestionnaireOptions($gettext),
      info: $gettext('If No, ignore data form 2 and go to question 3. If Yes, please complete data form 2. Please read Instruction II of the document carefully before filling in the form.')
    },
    has_produced: {
      label: `3. ${$gettext('Did your country produce CFCs, halons, carbon tetrachloride, methyl chloroform, HCFCs, HBFCs, bromochloromethane, methyl bromide or HFCs in the reporting year?')}`,
      type: 'questionnaireRadio',
      name: 'has_produced',
      selected: null,
      options: getCommonQuestionnaireOptions($gettext),
      info: $gettext('If No, ignore data form 3 and go to question 4. If Yes, please complete data form 3. Please read Instruction III of the document carefully before filling in the form.')
    },
    has_destroyed: {
      label: `4. ${$gettext('Did your country destroy any ozone-depleting substances or HFCs in the reporting year?')}`,
      type: 'questionnaireRadio',
      name: 'has_destroyed',
      selected: null,
      options: getCommonQuestionnaireOptions($gettext),
      info: $gettext('If No, ignore data form 4 and go to question 5. If Yes, please complete data form 4. Please read Instruction IV of the document carefully before filling in the form.')
    },
    has_nonparty: {
      label: `5. ${$gettext('Did your country import from or export or re-export to non-Parties in the reporting year?')}`,
      type: 'questionnaireRadio',
      name: 'has_nonparty',
      selected: null,
      options: getCommonQuestionnaireOptions($gettext),
      info: $gettext('If No, ignore data form 5 and go to question 6. If Yes, please complete data form 5. Please read instruction V (on data on imports from and exports to non-parties) of the data reporting instructions and guidelines document carefully, particularly the definition of non-parties, before filling in the form.')
    },
    has_emissions: {
      label: `6. ${$gettext('Did your country generate the substance HFC-23 in the reporting year from any facility that produces (manufactures) Annex C Group I or Annex F substances?')}`,
      type: 'questionnaireRadio',
      name: 'has_emissions',
      selected: null,
      options: getCommonQuestionnaireOptions($gettext),
      info: $gettext('If No, ignore data form 6. If Yes, please complete data form 6. Please read instruction VI (on data on emissions of Annex F Group II substance – HFC-23) of the data reporting instructions and guidelines document carefully before filling in the form.')
    }
  }
  return questionnaireFields
}
export {
  getQuestionnaireFields
}
