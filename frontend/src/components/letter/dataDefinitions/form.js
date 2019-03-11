import { getTabSubInfo } from '@/components/common/dataDefinitions/tabSubInfo'
import { setTabFiles } from '@/components/common/dataDefinitions/tabFiles'

const getFormLetter = ($gettext) => {
	const tabSubInfo = getTabSubInfo($gettext)
	const form = {
		formDetails: {
			tabsDisplay: ['sub_info', 'files'],
			dataNeeded: [
				'initialData.countryOptions',
				'initialData.countryOptionsSubInfo',
				'initialData.display.countries'
			]
		},
		tabs: {
			...setTabFiles($gettext),
			sub_info: {
				...tabSubInfo
			}
		}
	}
	return form
}

export {
	getFormLetter
}
