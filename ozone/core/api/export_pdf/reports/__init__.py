from .prodcons.prod_imp_exp import ProdImpExpReport
from .hfc_baseline import HFCBaselineReport
from ..art7 import Art7RawdataReport, Art7RawdataDiffReport
from ..art7 import BaselineHfcRawReport
from ..art7.labuse_report import LabUseReport
from .raf import RafReport
from .baseline_prod_cons import BaselineProdA5Report
from .baseline_prod_cons import BaselineConsA5Report
from .baseline_prod_cons import BaselineProdConsNA5Report
from .impexp_new_rec import ImpExpNewRecReport
from .impexp import ImportExportRecoveredSubstancesReport
from .impexp import ImportExportNewRecoveredAggregateReport
from .prodcons import ProdConsReport
from .prodcons import ProdConsByRegionReport
from .prodcons import ProdConsArt5SummaryReport
from .prodcons import ProdConsArt5PartiesReport
from .prodcons import ProdConsNonArt5PartiesReport

registry = [
    ProdConsReport,
    Art7RawdataReport,
    Art7RawdataDiffReport,
    LabUseReport,
    RafReport,
    ProdConsNonArt5PartiesReport,
    ProdConsArt5PartiesReport,
    ProdConsArt5SummaryReport,
    ProdConsByRegionReport,
    ProdImpExpReport,
    ImpExpNewRecReport,
    ImportExportNewRecoveredAggregateReport,
    ImportExportRecoveredSubstancesReport,
    BaselineProdA5Report,
    BaselineConsA5Report,
    BaselineProdConsNA5Report,
    BaselineHfcRawReport,
    HFCBaselineReport,
]

by_name = {r.name: r for r in registry}
