//  Permissions dictionary to describe whether or not an input is read-only
//    0 -> created by party, accesed by party
//    1 -> created by party, accesed by secretariat
//    2 -> created by secretariat, accesed by party
//    3 -> created by secretariat, accesed by secretariat
//
//    true  -> read-only
//    false -> not(read-only)
const permissions = {
  'reporting_channel': {
    'data_entry': [true, true, true, false],
    'submitted': [true, true, true, true],
    'processing': [true, true, true, true],
    'finalized': [true, true, true, true],
    'superseded': [true, true, true, true]
  },
  'submission_format': {
    'data_entry': [true, true, true, false],
    'submitted': [true, true, true, true],
    'processing': [true, true, true, true],
    'finalized': [true, true, true, true],
    'superseded': [true, true, true, true]
  },
  'reporting_officer': {
    'data_entry': [false, true, true, false],
    'submitted': [true, true, true, true],
    'processing': [true, true, true, true],
    'finalized': [true, true, true, true],
    'superseded': [true, true, true, true]
  },
  'submitted_at': {
    'data_entry': [true, true, true, false],
    'submitted': [true, true, true, true],
    'processing': [true, true, true, true],
    'finalized': [true, true, true, true],
    'superseded': [true, true, true, true]
  },
  'other_submission_info_data': {
    'data_entry': [false, true, true, false],
    'submitted': [true, true, true, true],
    'processing': [true, true, true, true],
    'finalized': [true, true, true, true],
    'superseded': [true, true, true, true]
  },
  'flag_provisional': {
    'data_entry': [false, true, true, false],
    'submitted': [true, false, true, false],
    'processing': [true, false, true, false],
    'finalized': [true, true, true, true],
    'superseded': [true, true, true, true]
  },
  'flag_blank': {
    'data_entry': [true, true, true, false],
    'submitted': [true, true, true, true],
    'processing': [true, false, true, false],
    'finalized': [true, true, true, true],
    'superseded': [true, true, true, true]
  },
  'flag_annex_group': {
    'data_entry': [false, true, true, false],
    'submitted': [true, true, true, true],
    'processing': [true, true, true, true],
    'finalized': [true, true, true, true],
    'superseded': [true, true, true, true]
  },
  'files': {
    'data_entry': [false, true, true, false],
    'submitted': [true, false, true, true],
    'processing': [true, false, true, false],
    'finalized': [true, true, true, true],
    'superseded': [true, true, true, true]
  },
  'questionnaire': {
    'data_entry': [false, true, true, false],
    'submitted': [true, true, true, true],
    'processing': [true, true, true, true],
    'finalized': [true, true, true, true],
    'superseded': [true, true, true, true]
  },
  'substance_data': {
    'data_entry': [false, true, true, false],
    'submitted': [true, true, true, true],
    'processing': [true, true, true, true],
    'finalized': [true, true, true, true],
    'superseded': [true, true, true, true]
  },
  'remarks_party': {
    'data_entry': [false, true, true, false],
    'submitted': [false, true, true, true],
    'processing': [false, true, true, true],
    'finalized': [true, true, true, true],
    'superseded': [true, true, true, true]
  },
  'remarks_secretariat': {
    'data_entry': [false, true, true, false],
    'submitted': [false, true, true, false],
    'processing': [false, true, true, false],
    'finalized': [true, true, true, true],
    'superseded': [true, true, true, true]
  }
}

const allowEditMode = () => {
  const editMode = {
    'data_entry': [false, false, false, false],
    'submitted': [false, false, false, false],
    'processing': [false, false, false, false],
    'finalized': [false, false, false, false],
    'superseded': [false, false, false, false]
  }
  Object.keys(permissions).forEach(dataType => {
    Object.keys(permissions[dataType]).forEach(submissionStatus => {
      for (
        let permissionsDictionaryIndex = 0;
        permissionsDictionaryIndex < permissions[dataType][submissionStatus].length;
        permissionsDictionaryIndex += 1
      ) {
        if (permissions[dataType][submissionStatus][permissionsDictionaryIndex] === false) {
          editMode[submissionStatus][permissionsDictionaryIndex] = true
          break
        }
      }
    })
  })
  return editMode
}

export {
  permissions,
  allowEditMode
}
