  # -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import Warning
import xml.etree.ElementTree as ET
import tempfile
import base64
from lxml import etree
import os
from datetime import datetime

class xmlStruct:
    class voucher:
        name = 'Comprobante'
        class transmitter:
            name = 'Emisor'
            def __init__(self, name, fiscReg, rfc):
                self.name = name
                self.fiscal_regimen = fiscReg
                self.rfc = rfc

            class transmitterStruct:
                Rfc = 'Rfc'
                Nombre = 'Nombre'
                RegimenFiscal = 'RegimenFiscal'

        class receiver:
            name = 'Receptor'
            def __init__(self, recFiscHome, name, fiscReg, rfc, cfdiUse):
                self.receiver_fiscal_home = recFiscHome
                self.name = name
                self.fiscal_regimen = fiscReg
                self.rfc = rfc
                self.cfdi_use = cfdiUse

            class receiverStruct:
                Rfc = 'Rfc'
                Nombre = 'Nombre'
                DomicilioFiscalReceptor = 'DomicilioFiscalReceptor'
                RegimenFiscalReceptor = 'RegimenFiscalReceptor'
                UsoCFDI = 'UsoCFDI'

        class concept:
            name = ['Conceptos', 'Concepto']
            class transport:
                name = ['Conceptos','Concepto','Impuestos','Traslados','Traslado']
                def __init__(self, base, tax, factorTyp, rateOrFee, amount):
                    self.base = base
                    self.tax = tax
                    self.factor_type = factorTyp
                    self.rate_or_fee = rateOrFee
                    self.amount = amount
                class conceptTransporStruct:
                    Base = 'Base'
                    Impuesto = 'Impuesto'
                    TipoFactor = 'TipoFactor'
                    TasaOCuota = 'TasaOCuota'
                    Importe = 'Importe'
            class retention:
                name = ['Conceptos','Concepto','Impuestos','Retenciones','Retencion']
                def __init__(self, base, tax, fctrTyp, rateOrFee, amount):
                    self.base = base
                    self.tax = tax
                    self.fact_type = fctrTyp
                    self.rate_or_fee = rateOrFee
                    self.amount = amount
                class conceptRetentionStruct:
                    Base = 'Base'
                    Impuesto = 'Impuesto'
                    TipoFactor = 'TipoFactor'
                    TasaOCuota = 'TasaOCuota'
                    Importe = 'Importe'

            def __init__ (self, prodServKey, identNo, qty, unitKey, 
                          unit, desc, unitVal, amount, disc, impObj):
                self.product_service_key = prodServKey
                self.identification_no = identNo
                self.quantity = qty
                self.unit_key = unitKey
                self.unit = unit
                self.description = desc
                self.unitary_value = unitVal
                self.amount = amount
                self.discount = disc
                self.imp_object = impObj
                self.Transport = ''
                self.Retetnion = ''

            class conceptStruct:
                ClaveProdServ = 'ClaveProdServ'
                NoIdentificacion = 'NoIdentificacion'
                Cantidad = 'Cantidad'
                ClaveUnidad = 'ClaveUnidad'
                Unidad = 'Unidad'
                Descripcion = 'Descripcion'
                ValorUnitario = 'ValorUnitario'
                Importe = 'Importe'
                Descuento = 'Descuento'
                ObjetoImp = 'ObjetoImp'

        class tax:
            name = 'Impuestos'
            class transport:
                name = ['Impuestos','Traslados','Traslado']
                def __init__(self, base, tax, facTyp, rateOrFee, amount):
                    self.base = base
                    self.tax = tax
                    self.factor_type = facTyp
                    self.rate_or_fee = rateOrFee
                    self.amount = amount
                class taxTransportStruct:
                    Base = 'Base'
                    Impuesto = 'Impuesto'
                    TipoFactor = 'TipoFactor'
                    TasaOCuota = 'TasaOCuota'
                    Importe = 'Importe'
            class retention:
                name = ['Impuestos','Retenciones','Retencion']
                def __init__(self,tax, amount):
                    self.tax = tax
                    self.amount = amount
                class taxRtentionStruct:
                    Impuesto = 'Impuesto'
                    Importe = 'Importe'
                    
            def __init__(self, ttlTranspTax, ttlDtaindTax):
                self.total_transport_tax = ttlTranspTax
                self.total_detained_tax = ttlDtaindTax

                self.Transport = ''
                self.Retention = ''
            
            class taxStruct:
                TotalImpuestosRetenidos = 'TotalImpuestosRetenidos'
                TotalImpuestosTrasladados = 'TotalImpuestosTrasladados'

        class complement:
            class digital_tax_stamp:
                name = ['Complemento','TimbreFiscalDigital']
                def __init__(self, uuid, stmpdDate, rfcPrvCer, cfdSeal, satCerNo, satSeal):
                    self.uuid = uuid
                    self.stamped_date = stmpdDate
                    self.rfc_prov_certificate = rfcPrvCer
                    self.cfd_seal = cfdSeal
                    self.sat_certificate_no = satCerNo
                    self.sat_seal = satSeal

                class complementDigitalTaxStampStruct:
                    Version = 'Version'
                    UUID = 'UUID'
                    FechaTimbrado = 'FechaTimbrado'
                    RfcProvCertif = 'RfcProvCertif'
                    SelloCFD = 'SelloCFD'
                    NoCertificadoSAT = 'NoCertificadoSAT'
                    SelloSAT = 'SelloSAT'

            class tax_bill:
                name = ['Complemento','CartaPorte']
                class locations:
                    name = ['Complemento','CartaPorte','Ubicaciones']

                    class location:
                        name = ['Complemento','CartaPorte','Ubicaciones','Ubicacion']
                        
                        class home:
                            name = ['Complemento','CartaPorte','Ubicaciones',
                                    'Ubicacion','Domicilio']
                            def __init__(self, strt, extNum, clny, 
                                         twn, state, cntry,pstlNum):
                                self.street = strt
                                self.externalNumber = extNum
                                self.colony = clny
                                self.town = twn
                                self.state = state
                                self.contry = cntry
                                self.postalNumber = pstlNum
                            class complementTaxBillLocationsLocationHomeStruct:
                                Calle = 'Calle'
                                NumeroExterior = 'NumeroExterior'
                                Colonia = 'Colonia'
                                Municipio = 'Municipio'
                                Estado = 'Estado'
                                Pais = 'Pais'
                                CodigoPostal = 'CodigoPostal'

                        def __init__(self, typLoc, rfcSendRecip, nmSendRecip, 
                                    dtTmDepArriv,idReNumTrib,fisclRes,distncTrvld):
                            self.typeLocation = typLoc
                            self.rfcSenderRecipient = rfcSendRecip
                            self.nameSenderRecipient = nmSendRecip
                            self.dateTimeDepartureArrival = dtTmDepArriv
                            self.tributaryIdRegisterNumber = idReNumTrib
                            self.fiscalResidence = fisclRes
                            self.traveldDistance = distncTrvld

                            self.Home = ''
                        
                        class complementTaxBillLocationsLocationStruct:
                            TipoUbicacion = 'TipoUbicacion'
                            RFCRemitenteDestinatario = 'RFCRemitenteDestinatario'
                            NombreRemitenteDestinatario = 'NombreRemitenteDestinatario'
                            FechaHoraSalidaLlegada = 'FechaHoraSalidaLlegada'
                            NumRegIdTrib = 'NumRegIdTrib'
                            ResidenciaFiscal= 'ResidenciaFiscal'
                            DistanciaRecorrida = 'DistanciaRecorrida'

                    def __init__(self):
                        self.Location = ''

                class merchandises:
                    name = ['Complemento','CartaPorte','Mercancias']

                    class merchindise:
                        name = ['Complemento','CartaPorte','Mercancias','Mercancia']
                        def __init__(self,trnsGood,dsc,qty,untCde,unit,
                                     kgWeigh,trifFrctn,matTyp):
                            self.transportGoods = trnsGood
                            self.description = dsc
                            self.quantity = qty
                            self.unitCode = untCde
                            self.unit = unit
                            self.kgWeight = kgWeigh
                            self.tariffFraction = trifFrctn
                            self.materialType = matTyp

                        class complementTaxBillMerchandisesMerchidiseStruct:
                            BienesTransp = 'BienesTransp'
                            Descripcion = 'Descripcion'
                            Cantidad = 'Cantidad'
                            ClaveUnidad = 'ClaveUnidad'
                            Unidad = 'Unidad'
                            MaterialPeligroso = 'MaterialPeligroso'
                            PesoEnKg = 'PesoEnKg'
                            FraccionArancelaria = 'FraccionArancelaria'
                            TipoMateria = 'TipoMateria'

                    class auto_transport:
                        name = ['Complemento','CartaPorte','Mercancias','Autotransporte']

                        class vehicle_Identification:
                            name = ['Complemento','CartaPorte','Mercancias',
                                    'Autotransporte','IdentificacionVehicular']
                            def __init__(self,veclCnfig,veclGrssWgth,
                                         vmPlt,anioMdlVm):
                                self.vehicleCOnfig = veclCnfig
                                self.vehicleGrossWeight = veclGrssWgth
                                self.vmPlate = vmPlt
                                self.anioModelVm = anioMdlVm

                        class complementTaxBillMerchandisesAutoTransportVehicleIdentificationStruct:
                                ConfigVehicular = 'ConfigVehicular'
                                PesoBrutoVehicular = 'PesoBrutoVehicular'
                                PlacaVM = 'PlacaVM'
                                AnioModeloVM = 'AnioModeloVM'

                        class insurance:
                            name = ['Complemento','CartaPorte','Mercancias',
                                    'Autotransporte','Seguros']
                            def __init__(self,civlRepInsur, civlRepPoliz):
                                self.civilRepresentationInsurance = civlRepInsur
                                self.civilRepresentationPoliza = civlRepPoliz
                            class complementTaxBillMerchandisesAutoTransportInsuranceStruct:
                                AseguraRespCivil = 'AseguraRespCivil'
                                PolizaRespCivil = 'PolizaRespCivil'

                        class trailers:
                            name = ['Complemento','CartaPorte','Mercancias',
                                    'Autotransporte','Remolques']
                            
                            class trailer:
                                name = ['Complemento','CartaPorte','Mercancias',
                                        'Autotransporte','Remolques','Remolque']
                                def __init__(self,trlSubTyp,plate):
                                    self.trailerSubType = trlSubTyp
                                    self.plate = plate
                                
                                class complementTaxBillMerchandisesAutoTransportTrailersTrailerStruct:
                                    SubTipoRem = 'SubTipoRem'
                                    Placa = 'Placa'

                            def __init__(self):
                                self.Trailer = ''

                        def __init__(self,prmSCT,numPermSCT):
                            self.permSCT = prmSCT
                            self.numPermission = numPermSCT

                            self.VehicleIdentification = ''
                            self.Insurance = ''
                            self.Trailers = ''

                        class complementTaxBillMerchandisesAutoTransportStruct:
                            PermSCT = 'PermSCT'
                            NumPermisoSCT = 'NumPermisoSCT'

                    def __init__(self,ttlGrssWeigh, weighUnt, ttlNtWeigh, ttlMerchNum):
                        self.totalGrossWeigh = ttlGrssWeigh
                        self.weighUnit = weighUnt
                        self.totalNetWeight = ttlNtWeigh
                        self.totalMerchadiseNumber = ttlMerchNum

                        self.Merchindise = ''
                        self.AutoTransport = ''

                    class complementTaxBillMerchandisesStruct:
                        PesoBrutoTotal = 'PesoBrutoTotal'
                        UnidadPeso = 'UnidadPeso'
                        PesoNetoTotal = 'PesoNetoTotal'
                        NumTotalMercancias = 'NumTotalMercancias'

                def __init__(self, version, idCCP, transInter, 
                             customsRegime, inOutMerc, countryOrig, 
                             inOutRoad, totalDistRec):
                    self.version = version
                    self.idCCP = idCCP
                    self.transInternac = transInter
                    self.customRegime = customsRegime
                    self.inOutMerc = inOutMerc
                    self.countryOrigin = countryOrig
                    self.inOutRoad = inOutRoad
                    self.totalDistRec = totalDistRec
                    self.Locations = ''
                    self.Merchandises = ''

                class complementTaxBillStruct:
                    Version = 'Version'
                    IdCCP = 'IdCCP'
                    TranspInternac = 'TranspInternac'
                    RegimenAduanero = 'RegimenAduanero'
                    EntradaSalidaMerc = 'EntradaSalidaMerc'
                    PaisOrigenDestino = 'PaisOrigenDestino'
                    ViaEntradaSalida = 'ViaEntradaSalida'
                    TotalDistRec = 'TotalDistRec'

            class payments:
                name = ['Complemento','Pagos']
                class totals:
                    name = ['Complemento','Pagos','Totales']

                    def __init__(self, totalPayments, totalIVARetention, 
                                 totalTransportIVA16Base, totalTransportIVA16Tax):
                        self.totalPayments = totalPayments
                        self.totalIVARetention = totalIVARetention
                        self.totalTransportIVA16Base = totalTransportIVA16Base
                        self.totalTransportIVA16Tax = totalTransportIVA16Tax

                    class paymentsTotalsStruct:
                        MontoTotalPagos = 'MontoTotalPagos'
                        TotalRetencionesIVA = 'TotalRetencionesIVA'
                        TotalTrasladosBaseIVA16 = 'TotalTrasladosBaseIVA16'
                        TotalTrasladosImpuestoIVA16 = 'TotalTrasladosImpuestoIVA16'

                class pay:
                    name = ['Complemento','Pagos','}Pago']

                    def __init__(self,paymentForm, formOfPayment, 
                                 currency, amount, typeOfChange):
                        self.paymentForm = paymentForm
                        self.formOfPayment = formOfPayment
                        self.currency = currency
                        self.amount = amount
                        self.typeOfChange = typeOfChange

                        self.RelatedDocument = ''
                        self.TaxPRetention = ''
                        self.TaxPTransport = ''

                    class relatedDocuments:
                        name = ['Complemento','Pagos','}Pago','DoctoRelacionado']

                        def __init__(self,drEq,invoice,idDoc,amountPayed,
                                     pendingAmount,unsolvedAmount,currency,
                                     partialityNum,objctTaxDR):
                            self.drEquivalence = drEq
                            self.invoice = invoice
                            self.idDoc = idDoc
                            self.amountPayed = amountPayed
                            self.pendingAmount = pendingAmount
                            self.unsolvedAmount = unsolvedAmount
                            self.currency = currency
                            self.partialityNum = partialityNum
                            self.objectTaxDR = objctTaxDR
                            self.RetentionTaxDR = ''
                            self.TreansportTaxDR = ''

                        class relatedDocTaxRetention:
                            name = ['Complemento','Pagos','}Pago','DoctoRelacionado','ImpuestosDR','RetencionesDR','RetencionDR']
                            
                            def __init__(self,baseDR,importDR,taxDR,
                                         rateOrFeeDR,factorTypeDR):
                                self.baseDR = baseDR
                                self.importDR = importDR
                                self.taxDR = taxDR
                                self.rateOrFeeDR = rateOrFeeDR
                                self.factorTypeDR = factorTypeDR

                            class relatedDocTaxRetentionStruct:
                                BaseDR = 'BaseDR'
                                ImporteDR = 'ImporteDR'
                                ImpuestoDR = 'ImpuestoDR'
                                TasaOCuotaDR = 'TasaOCuotaDR'
                                TipoFactorDR = 'TipoFactorDR'

                        class relatedDocTaxTransport:
                            name = ['Complemento','Pagos','}Pago','DoctoRelacionado','ImpuestosDR','TrasladosDR','TrasladoDR']
                            
                            def __init__(self,baseDR,importDR,taxDR,
                                         rateOrFeeDR,factorTypeDR):
                                self.baseDR = baseDR
                                self.importDR = importDR
                                self.taxDR = taxDR
                                self.rateOrFeeDR = rateOrFeeDR
                                self.factorTypeDR = factorTypeDR
                            
                            class relatedDocTaxTransportStruct:
                                BaseDR = 'BaseDR'
                                ImporteDR = 'ImporteDR'
                                ImpuestoDR = 'ImpuestoDR'
                                TasaOCuotaDR = 'TasaOCuotaDR'
                                TipoFactorDR = 'TipoFactorDR'
                           
                            #
                        class relatedDocumentsStruct:
                            name = ['Pagos','Egresos','Ingresos']
                            EquivalenciaDR = 'EquivalenciaDR'
                            Folio = 'Folio'
                            IdDocumento = 'IdDocumento'
                            ImpPagado = 'ImpPagado'
                            ImpSaldoAnt = 'ImpSaldoAnt'
                            ImpSaldoInsoluto = 'ImpSaldoInsoluto'
                            MonedaDR = 'MonedaDR'
                            NumParcialidad = 'NumParcialidad'
                            ObjetoImpDR = 'ObjetoImpDR'

                        
                    class taxPRetention:
                        name = ['Complemento','Pagos','}Pago','ImpuestosP','RetencionesP','RetencionP']
                        def __init__(self, importP, taxP):
                            self.importP = importP
                            self.taxP = taxP

                        class taxPRetentionStruct:
                            ImporteP = 'ImporteP'
                            ImpuestoP = 'ImpuestoP'

                    class taxPTransport:
                        name = ['Complemento','Pagos','}Pago','ImpuestosP','TrasladosP','TrasladoP']
                        def __init__(self,baseP,importP,taxP,rateOrFeeP,factorTypeP):
                            self.baseP = baseP
                            self.importP = importP
                            self.taxP = taxP
                            self.rateOrFeeP = rateOrFeeP
                            self.factorTypeP = factorTypeP

                        class taxPTransportStruct:
                            BaseP = 'BaseP'
                            ImporteP = 'ImporteP'
                            ImpuestoP = 'ImpuestoP'
                            TasaOCuotaP = 'TasaOCuotaP'
                            TipoFactorP = 'TipoFactorP'

                    class paymentsPayStruct:
                        FechaPago = 'FechaPago'
                        FormaDePagoP = 'FormaDePagoP'
                        MonedaP = 'MonedaP'
                        Monto = 'Monto'
                        TipoCambioP = 'TipoCambioP'

                def __init__(self, version):
                    self.version = version

                    self.Totals = ''
                    self.Pay = ''

                class paymentsStruct:
                    Version = 'Version'

            def __init__(self):
                self.Digital_Tax_Stamp = ''
                self.Tax_bill = ''
                self.Payments = ''

        
        def __init__(self, cert, payCond, exp, 
                     date, inv, payForm, expePlace, 
                     payMethod, curren, certNo, seal, 
                     ser, subTotal, vouchTyp, total,
                     disc, chngTyp):
            self.certificate = cert
            self.payment_conditions = payCond
            self.export = exp
            self.date = date
            self.invoice = inv
            self.payment_form = payForm
            self.expedition_place = expePlace
            self.payment_method = payMethod
            self.currency = curren
            self.certificate_no = certNo
            self.seal = seal
            self.series = ser
            self.sub_total = subTotal
            self.voucher_type = vouchTyp
            self.total = total   
            self.discount = disc
            self.changeTipe = chngTyp

            self.Transmitter = '' 
            self.Receiver = ''
            self.Concept = ''
            self.Tax = ''
            self.Complement = ''
            
        class voucherSruct():
            Version = 'Version'
            Serie = 'Serie'
            Folio = 'Folio'
            Fecha = 'Fecha'
            Sello = 'Sello'
            FormaPago = 'FormaPago'
            NoCertificado = 'NoCertificado'
            Certificado = 'Certificado'
            SubTotal = 'SubTotal'
            Descuento = 'Descuento'
            Moneda = 'Moneda'
            Total = 'Total'
            TipoDeComprobante = 'TipoDeComprobante'
            Exportacion = 'Exportacion'
            MetodoPago = 'MetodoPago'
            LugarExpedicion = 'LugarExpedicion'
            CondicionesDePago = 'CondicinesDePago'
            TipoCambio = 'TipoCambio'

    def __init__(self):
        self.Voucher = ''

    def createXMLStruct(self, xmlTreeRoot):
        self.Voucher = self.voucher(
            cert        = xmlTreeRoot.getAttribute(self.voucher.voucherSruct.Certificado),
            payCond     = xmlTreeRoot.getAttribute(self.voucher.voucherSruct.CondicionesDePago),
            exp         = xmlTreeRoot.getAttribute(self.voucher.voucherSruct.Exportacion),
            date        = xmlTreeRoot.getAttribute(self.voucher.voucherSruct.Fecha),
            inv         = xmlTreeRoot.getAttribute(self.voucher.voucherSruct.Folio),
            payForm     = xmlTreeRoot.getAttribute(self.voucher.voucherSruct.FormaPago),
            expePlace   = xmlTreeRoot.getAttribute(self.voucher.voucherSruct.LugarExpedicion),
            payMethod   = xmlTreeRoot.getAttribute(self.voucher.voucherSruct.MetodoPago),
            curren      = xmlTreeRoot.getAttribute(self.voucher.voucherSruct.Moneda),
            certNo      = xmlTreeRoot.getAttribute(self.voucher.voucherSruct.NoCertificado),
            seal        = xmlTreeRoot.getAttribute(self.voucher.voucherSruct.Sello),
            ser         = xmlTreeRoot.getAttribute(self.voucher.voucherSruct.Serie),
            subTotal    = xmlTreeRoot.getAttribute(self.voucher.voucherSruct.SubTotal),
            vouchTyp    = xmlTreeRoot.getAttribute(self.voucher.voucherSruct.TipoDeComprobante),
            total       = xmlTreeRoot.getAttribute(self.voucher.voucherSruct.Total),
            disc        = xmlTreeRoot.getAttribute(self.voucher.voucherSruct.Descuento),
            chngTyp     = xmlTreeRoot.getAttribute(self.voucher.voucherSruct.TipoCambio)
            )
        
        auxProperty = xmlTreeRoot
        if isinstance(self.voucher.transmitter.name, list):
            for names in self.voucher.transmitter.name:
                auxProperty = auxProperty.getProperty(names)
            transmitterProperty = auxProperty
        else:
            transmitterProperty = auxProperty.getProperty(self.voucher.transmitter.name)

        self.Voucher.Transmitter = self.voucher.transmitter(
            name        = transmitterProperty.getAttribute(self.voucher.transmitter.transmitterStruct.Nombre),
            fiscReg     = transmitterProperty.getAttribute(self.voucher.transmitter.transmitterStruct.RegimenFiscal),
            rfc         = transmitterProperty.getAttribute(self.voucher.transmitter.transmitterStruct.Rfc)
        )


        auxProperty = xmlTreeRoot
        if isinstance(self.voucher.receiver.name, list):
            for names in self.voucher.receiver.name:
                auxProperty = auxProperty.getProperty(names)
            receiverProperty = auxProperty
        else:
            receiverProperty = auxProperty.getProperty(self.voucher.receiver.name)

        self.Voucher.Receiver = self.voucher.receiver(
            recFiscHome = receiverProperty.getAttribute(self.voucher.receiver.receiverStruct.DomicilioFiscalReceptor),
            name        = receiverProperty.getAttribute(self.voucher.receiver.receiverStruct.Nombre),
            fiscReg     = receiverProperty.getAttribute(self.voucher.receiver.receiverStruct.RegimenFiscalReceptor),
            rfc         = receiverProperty.getAttribute(self.voucher.receiver.receiverStruct.Rfc),
            cfdiUse     = receiverProperty.getAttribute(self.voucher.receiver.receiverStruct.UsoCFDI),
        )

        
        self.Voucher.Concept = []
        for concepts in xmlTreeRoot.root:
            if self.voucher.concept.name[0] in concepts.tag: 
                auxConcept = getSafeAttribute(concepts)
                for concept in auxConcept.root:
                    finalConcept = getSafeAttribute(concept)
                    auxProperty = finalConcept
                    if isinstance(self.voucher.concept.name, list):
                        for names in self.voucher.concept.name:
                            auxProperty = auxProperty.getProperty(names)
                        conceptProperty = auxProperty
                    else:
                        conceptProperty = auxProperty.getProperty(self.voucher.concept.name)
                        
                    newConcept = self.voucher.concept(
                        prodServKey = conceptProperty.getAttribute(self.voucher.concept.conceptStruct.ClaveProdServ),
                        identNo     = conceptProperty.getAttribute(self.voucher.concept.conceptStruct.NoIdentificacion),
                        qty         = conceptProperty.getAttribute(self.voucher.concept.conceptStruct.Cantidad),
                        unitKey     = conceptProperty.getAttribute(self.voucher.concept.conceptStruct.ClaveUnidad),
                        unit        = conceptProperty.getAttribute(self.voucher.concept.conceptStruct.Unidad),
                        desc        = conceptProperty.getAttribute(self.voucher.concept.conceptStruct.Descripcion),
                        unitVal     = conceptProperty.getAttribute(self.voucher.concept.conceptStruct.ValorUnitario),
                        amount      = conceptProperty.getAttribute(self.voucher.concept.conceptStruct.Importe),
                        disc        = conceptProperty.getAttribute(self.voucher.concept.conceptStruct.Descuento),
                        impObj      = conceptProperty.getAttribute(self.voucher.concept.conceptStruct.ObjetoImp)       
                    )

                    auxProperty = xmlTreeRoot 
                    if isinstance(self.voucher.concept.transport.name, list):
                        for names in self.voucher.concept.transport.name:
                            auxProperty = auxProperty.getProperty(names)
                        conceptTransitProperty = auxProperty
                    else:
                        conceptTransitProperty = auxProperty.getProperty(self.voucher.concept.transport.name)

                    newConcept.Transport = self.voucher.concept.transport(
                        base        = conceptTransitProperty.getAttribute(self.voucher.concept.transport.conceptTransporStruct.Base),
                        tax         = conceptTransitProperty.getAttribute(self.voucher.concept.transport.conceptTransporStruct.Impuesto),
                        factorTyp   = conceptTransitProperty.getAttribute(self.voucher.concept.transport.conceptTransporStruct.TipoFactor),
                        rateOrFee   = conceptTransitProperty.getAttribute(self.voucher.concept.transport.conceptTransporStruct.TasaOCuota),
                        amount      = conceptTransitProperty.getAttribute(self.voucher.concept.transport.conceptTransporStruct.Importe)
                    )

                    newConcept.Retetnion = []
                    auxProperty = xmlTreeRoot 

                    for concepts in  xmlTreeRoot.root:
                        if self.voucher.concept.retention.name[0] in concepts.tag:
                            auxConcept = getSafeAttribute(concepts)
                            for concept in auxConcept.root:
                                if self.voucher.concept.retention.name[1] in concept.tag:
                                    auxConcept = getSafeAttribute(concept)
                                    for tax in auxConcept.root:
                                        if self.voucher.concept.retention.name[2] in tax.tag:
                                            auxConcept = getSafeAttribute(tax)
                                            for retentions in auxConcept.root:
                                                if self.voucher.concept.retention.name[3] in retentions.tag:
                                                    auxConcept = getSafeAttribute(retentions)
                                                    for retention in auxConcept.root:
                                                        if self.voucher.concept.retention.name[4] in retention.tag:
                                                            auxProperty = getSafeAttribute(retention)
                                                            newConcept.Retetnion.append(self.voucher.concept.retention(
                                                                base        = auxProperty.getAttribute(self.voucher.concept.retention.conceptRetentionStruct.Base),
                                                                tax         = auxProperty.getAttribute(self.voucher.concept.retention.conceptRetentionStruct.Impuesto),
                                                                fctrTyp     = auxProperty.getAttribute(self.voucher.concept.retention.conceptRetentionStruct.TipoFactor),
                                                                rateOrFee   = auxProperty.getAttribute(self.voucher.concept.retention.conceptRetentionStruct.TasaOCuota),
                                                                amount      = auxProperty.getAttribute(self.voucher.concept.retention.conceptRetentionStruct.Importe),
                                                            ))

                    self.Voucher.Concept.append(newConcept)

        auxProperty = xmlTreeRoot 
        if isinstance(self.voucher.tax.name, list):
            for names in self.voucher.tax.name:
                auxProperty = auxProperty.getProperty(names)
            taxProperty = auxProperty
        else:
            taxProperty = auxProperty.getProperty(self.voucher.tax.name)
        
        self.Voucher.Tax = self.voucher.tax(
            ttlTranspTax= taxProperty.getAttribute(self.voucher.tax.taxStruct.TotalImpuestosTrasladados),
            ttlDtaindTax= taxProperty.getAttribute(self.voucher.tax.taxStruct.TotalImpuestosRetenidos)
        )

        auxProperty = xmlTreeRoot 
        if isinstance(self.voucher.tax.transport.name, list):
            for names in self.voucher.tax.transport.name:
                auxProperty = auxProperty.getProperty(names)
            taxTransportProperty = auxProperty
        else:
            taxTransportProperty = auxProperty.getProperty(self.voucher.tax.transport.name)

        self.Voucher.Tax.Transport = self.voucher.tax.transport(
            base        = taxTransportProperty.getAttribute(self.voucher.tax.transport.taxTransportStruct.Base),
            tax         = taxTransportProperty.getAttribute(self.voucher.tax.transport.taxTransportStruct.Impuesto),
            facTyp      = taxTransportProperty.getAttribute(self.voucher.tax.transport.taxTransportStruct.TipoFactor),
            rateOrFee   = taxTransportProperty.getAttribute(self.voucher.tax.transport.taxTransportStruct.TasaOCuota),
            amount      = taxTransportProperty.getAttribute(self.voucher.tax.transport.taxTransportStruct.Importe)
        )

        self.Voucher.Tax.Retention = []
        auxProperty = xmlTreeRoot 
        for concept in auxProperty.root:
            if self.voucher.tax.retention.name[0] in concept.tag:
                auxProperty = getSafeAttribute(concept)
                for tax in auxProperty.root:
                    if self.voucher.tax.retention.name[1] in tax.tag:
                        auxProperty = getSafeAttribute(tax)
                        for retentions in auxProperty.root:
                            if self.voucher.tax.retention.name[2] in retentions:
                                auxProperty = auxProperty.getProperty(self.voucher.tax.retention.name[2])
                                self.Voucher.Tax.Retention.append(self.voucher.tax.retention(
                                    tax     = auxProperty.getAttribute(self.voucher.tax.retention.taxRtentionStruct.Impuesto),
                                    amount  = auxProperty.getAttribute(self.voucher.tax.retention.taxRtentionStruct.Importe)
                                ))

        auxProperty = xmlTreeRoot 
        if isinstance(self.voucher.complement.digital_tax_stamp.name, list):
            for names in self.voucher.complement.digital_tax_stamp.name:
                auxProperty = auxProperty.getProperty(names)
            complementProperty = auxProperty
        else:
            complementProperty = auxProperty.getProperty(self.voucher.complement.digital_tax_stamp.name)

        self.Voucher.Complement = self.voucher.complement()
        self.Voucher.Complement.Digital_Tax_Stamp = self.voucher.complement.digital_tax_stamp(
            uuid        = complementProperty.getAttribute(self.voucher.complement.digital_tax_stamp.complementDigitalTaxStampStruct.UUID),
            stmpdDate   = complementProperty.getAttribute(self.voucher.complement.digital_tax_stamp.complementDigitalTaxStampStruct.FechaTimbrado),
            rfcPrvCer   = complementProperty.getAttribute(self.voucher.complement.digital_tax_stamp.complementDigitalTaxStampStruct.RfcProvCertif),
            cfdSeal     = complementProperty.getAttribute(self.voucher.complement.digital_tax_stamp.complementDigitalTaxStampStruct.SelloCFD),
            satCerNo    = complementProperty.getAttribute(self.voucher.complement.digital_tax_stamp.complementDigitalTaxStampStruct.NoCertificadoSAT),
            satSeal     = complementProperty.getAttribute(self.voucher.complement.digital_tax_stamp.complementDigitalTaxStampStruct.SelloSAT)
        )

        auxProperty = xmlTreeRoot 
        if isinstance(self.voucher.complement.tax_bill.name, list):
            for names in self.voucher.complement.tax_bill.name:
                auxProperty = auxProperty.getProperty(names)
            complementProperty = auxProperty
        else:
            complementProperty = auxProperty.getProperty(self.voucher.complement.tax_bill.name)

        self.Voucher.Complement.Tax_bill = self.voucher.complement.tax_bill(
            version         = complementProperty.getAttribute(self.voucher.complement.tax_bill.complementTaxBillStruct.Version),
            idCCP           = complementProperty.getAttribute(self.voucher.complement.tax_bill.complementTaxBillStruct.IdCCP),
            transInter      = complementProperty.getAttribute(self.voucher.complement.tax_bill.complementTaxBillStruct.TranspInternac),
            customsRegime   = complementProperty.getAttribute(self.voucher.complement.tax_bill.complementTaxBillStruct.RegimenAduanero),
            inOutMerc       = complementProperty.getAttribute(self.voucher.complement.tax_bill.complementTaxBillStruct.EntradaSalidaMerc),
            countryOrig     = complementProperty.getAttribute(self.voucher.complement.tax_bill.complementTaxBillStruct.PaisOrigenDestino),
            inOutRoad       = complementProperty.getAttribute(self.voucher.complement.tax_bill.complementTaxBillStruct.ViaEntradaSalida),
            totalDistRec    = complementProperty.getAttribute(self.voucher.complement.tax_bill.complementTaxBillStruct.TotalDistRec)
        )

        for complements in complementProperty.root:
            if self.voucher.complement.tax_bill.locations.name[2] in complements.tag:
                otherProperty = getSafeAttribute(complements)
                self.Voucher.Complement.Tax_bill.Locations = self.voucher.complement.tax_bill.locations()
                self.Voucher.Complement.Tax_bill.Locations.Location = []

                for location in otherProperty.root:
                    locationSafeProperty = getSafeAttribute(location)
                    newLocation = self.voucher.complement.tax_bill.locations.location(
                        typLoc              = locationSafeProperty.getAttribute(self.voucher.complement.tax_bill.locations.location.complementTaxBillLocationsLocationStruct.TipoUbicacion),
                        rfcSendRecip        = locationSafeProperty.getAttribute(self.voucher.complement.tax_bill.locations.location.complementTaxBillLocationsLocationStruct.RFCRemitenteDestinatario),
                        nmSendRecip         = locationSafeProperty.getAttribute(self.voucher.complement.tax_bill.locations.location.complementTaxBillLocationsLocationStruct.NombreRemitenteDestinatario),
                        dtTmDepArriv        = locationSafeProperty.getAttribute(self.voucher.complement.tax_bill.locations.location.complementTaxBillLocationsLocationStruct.FechaHoraSalidaLlegada),
                        idReNumTrib         = locationSafeProperty.getAttribute(self.voucher.complement.tax_bill.locations.location.complementTaxBillLocationsLocationStruct.NumRegIdTrib),
                        fisclRes            = locationSafeProperty.getAttribute(self.voucher.complement.tax_bill.locations.location.complementTaxBillLocationsLocationStruct.ResidenciaFiscal),
                        distncTrvld         = locationSafeProperty.getAttribute(self.voucher.complement.tax_bill.locations.location.complementTaxBillLocationsLocationStruct.DistanciaRecorrida)
                    )

                    for home in locationSafeProperty.root:
                        homeSafeProperty = getSafeAttribute(home)
                        newLocation.Home = self.voucher.complement.tax_bill.locations.location.home(
                            strt            = homeSafeProperty.getAttribute(self.voucher.complement.tax_bill.locations.location.home.complementTaxBillLocationsLocationHomeStruct.Calle),
                            extNum          = homeSafeProperty.getAttribute(self.voucher.complement.tax_bill.locations.location.home.complementTaxBillLocationsLocationHomeStruct.NumeroExterior),
                            clny            = homeSafeProperty.getAttribute(self.voucher.complement.tax_bill.locations.location.home.complementTaxBillLocationsLocationHomeStruct.Colonia),
                            twn             = homeSafeProperty.getAttribute(self.voucher.complement.tax_bill.locations.location.home.complementTaxBillLocationsLocationHomeStruct.Municipio),
                            state           = homeSafeProperty.getAttribute(self.voucher.complement.tax_bill.locations.location.home.complementTaxBillLocationsLocationHomeStruct.Estado),
                            cntry           = homeSafeProperty.getAttribute(self.voucher.complement.tax_bill.locations.location.home.complementTaxBillLocationsLocationHomeStruct.Pais),
                            pstlNum         = homeSafeProperty.getAttribute(self.voucher.complement.tax_bill.locations.location.home.complementTaxBillLocationsLocationHomeStruct.CodigoPostal)
                        )

                    self.Voucher.Complement.Tax_bill.Locations.Location.append(newLocation)

            elif self.voucher.complement.tax_bill.merchandises.name[2] in complements.tag:
                merchandiseProperty = getSafeAttribute(complements)
                self.Voucher.Complement.Tax_bill.Merchandises = self.voucher.complement.tax_bill.merchandises(
                    ttlGrssWeigh        = merchandiseProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.complementTaxBillMerchandisesStruct.PesoBrutoTotal),
                    weighUnt            = merchandiseProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.complementTaxBillMerchandisesStruct.UnidadPeso),
                    ttlNtWeigh          = merchandiseProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.complementTaxBillMerchandisesStruct.PesoNetoTotal),
                    ttlMerchNum         = merchandiseProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.complementTaxBillMerchandisesStruct.NumTotalMercancias),
                )
                self.Voucher.Complement.Tax_bill.Merchandises.Merchindise = []
                for merchOrAutoTrens in merchandiseProperty.root:
                    if self.voucher.complement.tax_bill.merchandises.merchindise.name[3] in merchOrAutoTrens.tag:
                        merchProperty = getSafeAttribute(merchOrAutoTrens)
                        nerMerch = self.voucher.complement.tax_bill.merchandises.merchindise(
                            trnsGood    = merchProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.merchindise.complementTaxBillMerchandisesMerchidiseStruct.BienesTransp),
                            dsc         = merchProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.merchindise.complementTaxBillMerchandisesMerchidiseStruct.Descripcion),
                            qty         = merchProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.merchindise.complementTaxBillMerchandisesMerchidiseStruct.Cantidad),
                            untCde      = merchProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.merchindise.complementTaxBillMerchandisesMerchidiseStruct.ClaveUnidad),
                            unit        = merchProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.merchindise.complementTaxBillMerchandisesMerchidiseStruct.Unidad),
                            kgWeigh     = merchProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.merchindise.complementTaxBillMerchandisesMerchidiseStruct.MaterialPeligroso),
                            trifFrctn   = merchProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.merchindise.complementTaxBillMerchandisesMerchidiseStruct.FraccionArancelaria),
                            matTyp      = merchProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.merchindise.complementTaxBillMerchandisesMerchidiseStruct.TipoMateria)
                        )
                        self.Voucher.Complement.Tax_bill.Merchandises.Merchindise.append(nerMerch)
                    elif self.voucher.complement.tax_bill.merchandises.auto_transport.name[3] in merchOrAutoTrens.tag:
                        autoTransProperty = getSafeAttribute(merchOrAutoTrens)
                        self.Voucher.Complement.Tax_bill.Merchandises.AutoTransport = self.voucher.complement.tax_bill.merchandises.auto_transport(
                            prmSCT      = autoTransProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.auto_transport.complementTaxBillMerchandisesAutoTransportStruct.PermSCT),
                            numPermSCT  = autoTransProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.auto_transport.complementTaxBillMerchandisesAutoTransportStruct.NumPermisoSCT)
                        )

                        for identificationInsuranceOrTrailer in autoTransProperty.root:
                            if self.voucher.complement.tax_bill.merchandises.auto_transport.vehicle_Identification.name[4] in identificationInsuranceOrTrailer.tag:
                                autebtificationProperty = getSafeAttribute(identificationInsuranceOrTrailer)
                                self.Voucher.Complement.Tax_bill.Merchandises.AutoTransport.VehicleIdentification = self.voucher.complement.tax_bill.merchandises.auto_transport.vehicle_Identification(
                                    veclCnfig       = autebtificationProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.auto_transport.vehicle_Identification.complementTaxBillMerchandisesAutoTransportVehicleIdentificationStruct.ConfigVehicular),
                                    veclGrssWgth    = autebtificationProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.auto_transport.vehicle_Identification.complementTaxBillMerchandisesAutoTransportVehicleIdentificationStruct.PesoBrutoVehicular),
                                    vmPlt           = autebtificationProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.auto_transport.vehicle_Identification.complementTaxBillMerchandisesAutoTransportVehicleIdentificationStruct.PlacaVM),
                                    anioMdlVm       = autebtificationProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.auto_transport.vehicle_Identification.complementTaxBillMerchandisesAutoTransportVehicleIdentificationStruct.AnioModeloVM)
                                )
                            elif self.voucher.complement.tax_bill.merchandises.auto_transport.insurance.name[4] in identificationInsuranceOrTrailer.tag:
                                insuranceProperty = getSafeAttribute(identificationInsuranceOrTrailer)
                                self.Voucher.Complement.Tax_bill.Merchandises.AutoTransport.Insurance = self.voucher.complement.tax_bill.merchandises.auto_transport.insurance(
                                    civlRepInsur    = insuranceProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.auto_transport.insurance.complementTaxBillMerchandisesAutoTransportInsuranceStruct.AseguraRespCivil),
                                    civlRepPoliz    = insuranceProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.auto_transport.insurance.complementTaxBillMerchandisesAutoTransportInsuranceStruct.PolizaRespCivil),
                                )
                            elif self.voucher.complement.tax_bill.merchandises.auto_transport.trailers.name[4] in identificationInsuranceOrTrailer.tag:
                                trailersProperty = getSafeAttribute(identificationInsuranceOrTrailer)
                                self.Voucher.Complement.Tax_bill.Merchandises.AutoTransport.Trailers = self.voucher.complement.tax_bill.merchandises.auto_transport.trailers()
                                for trailer in trailersProperty.root:
                                    trailerProperty = getSafeAttribute(trailer)
                                    self.Voucher.Complement.Tax_bill.Merchandises.AutoTransport.Trailers.Trailer = self.voucher.complement.tax_bill.merchandises.auto_transport.trailers.trailer(
                                      trlSubTyp =  trailerProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.auto_transport.trailers.trailer.complementTaxBillMerchandisesAutoTransportTrailersTrailerStruct.SubTipoRem), 
                                      plate =  trailerProperty.getAttribute(self.voucher.complement.tax_bill.merchandises.auto_transport.trailers.trailer.complementTaxBillMerchandisesAutoTransportTrailersTrailerStruct.Placa), 
                                    )
        
        auxProperty = xmlTreeRoot 
        if isinstance(self.voucher.complement.payments.name, list):
            for names in self.voucher.complement.payments.name:
                auxProperty = auxProperty.getProperty(names)
            complementProperty = auxProperty
        else:
            complementProperty = auxProperty.getProperty(self.voucher.complement.payments.name)

        self.Voucher.Complement.Payments = self.voucher.complement.payments(
            version =  complementProperty.getAttribute(self.voucher.complement.payments.paymentsStruct.Version)
        )

        auxProperty = xmlTreeRoot 
        if isinstance(self.voucher.complement.payments.totals.name, list):
            for names in self.voucher.complement.payments.totals.name:
                auxProperty = auxProperty.getProperty(names)
            complementProperty = auxProperty
        else:
            complementProperty = auxProperty.getProperty(self.voucher.complement.payments.totals.name)

        self.Voucher.Complement.Payments.Totals = self.voucher.complement.payments.totals(
            totalPayments = complementProperty.getAttribute(self.voucher.complement.payments.totals.paymentsTotalsStruct.MontoTotalPagos),
            totalIVARetention = complementProperty.getAttribute(self.voucher.complement.payments.totals.paymentsTotalsStruct.TotalRetencionesIVA),
            totalTransportIVA16Base = complementProperty.getAttribute(self.voucher.complement.payments.totals.paymentsTotalsStruct.TotalTrasladosBaseIVA16),
            totalTransportIVA16Tax = complementProperty.getAttribute(self.voucher.complement.payments.totals.paymentsTotalsStruct.TotalTrasladosImpuestoIVA16),
        )

        auxProperty = xmlTreeRoot 
        if isinstance(self.voucher.complement.payments.pay.name, list):
            for names in self.voucher.complement.payments.pay.name:
                auxProperty = auxProperty.getProperty(names)
            complementProperty = auxProperty
        else:
            complementProperty = auxProperty.getProperty(self.voucher.complement.payments.pay.name)
        
        self.Voucher.Complement.Payments.Pay = self.voucher.complement.payments.pay(
            paymentForm = complementProperty.getAttribute(self.voucher.complement.payments.pay.paymentsPayStruct.FechaPago),
            formOfPayment = complementProperty.getAttribute(self.voucher.complement.payments.pay.paymentsPayStruct.FormaDePagoP),
            currency = complementProperty.getAttribute(self.voucher.complement.payments.pay.paymentsPayStruct.MonedaP),
            amount = complementProperty.getAttribute(self.voucher.complement.payments.pay.paymentsPayStruct.Monto),
            typeOfChange = complementProperty.getAttribute(self.voucher.complement.payments.pay.paymentsPayStruct.TipoCambioP)
        )

        self.Voucher.Complement.Payments.Pay.RelatedDocument = []
        for docRelatedOrTaxP in complementProperty.root:
            if self.voucher.complement.payments.pay.relatedDocuments.name[3] in docRelatedOrTaxP.tag:
                otherProperty = getSafeAttribute(docRelatedOrTaxP)
                
                newRelatedDoc = self.voucher.complement.payments.pay.relatedDocuments(
                    drEq = otherProperty.getAttribute(self.voucher.complement.payments.pay.relatedDocuments.relatedDocumentsStruct.EquivalenciaDR),
                    invoice = otherProperty.getAttribute(self.voucher.complement.payments.pay.relatedDocuments.relatedDocumentsStruct.Folio),
                    idDoc = otherProperty.getAttribute(self.voucher.complement.payments.pay.relatedDocuments.relatedDocumentsStruct.IdDocumento),
                    amountPayed = otherProperty.getAttribute(self.voucher.complement.payments.pay.relatedDocuments.relatedDocumentsStruct.ImpPagado),
                    pendingAmount = otherProperty.getAttribute(self.voucher.complement.payments.pay.relatedDocuments.relatedDocumentsStruct.ImpSaldoAnt),
                    unsolvedAmount = otherProperty.getAttribute(self.voucher.complement.payments.pay.relatedDocuments.relatedDocumentsStruct.ImpSaldoInsoluto),
                    currency = otherProperty.getAttribute(self.voucher.complement.payments.pay.relatedDocuments.relatedDocumentsStruct.MonedaDR),
                    partialityNum = otherProperty.getAttribute(self.voucher.complement.payments.pay.relatedDocuments.relatedDocumentsStruct.NumParcialidad),
                    objctTaxDR = otherProperty.getAttribute(self.voucher.complement.payments.pay.relatedDocuments.relatedDocumentsStruct.ObjetoImpDR)
                )

                for taxes in otherProperty.root:
                    if self.voucher.complement.payments.pay.relatedDocuments.relatedDocTaxRetention.name[4] in taxes.tag:
                        internalTaxProp = getSafeAttribute(taxes)
                        for tax in internalTaxProp.root:
                            if self.voucher.complement.payments.pay.relatedDocuments.relatedDocTaxRetention.name[5] in tax.tag:
                                inertnalTaxesTaxProperty = getSafeAttribute(tax)
                                for retentionDR in inertnalTaxesTaxProperty.root:
                                    if self.voucher.complement.payments.pay.relatedDocuments.relatedDocTaxRetention.name[6] in retentionDR.tag:
                                        inertnalTaxesTaxProperty = getSafeAttribute(retentionDR)

                                        newRelatedDoc.RetentionTaxDR = self.voucher.complement.payments.pay.relatedDocuments.relatedDocTaxRetention(
                                            baseDR = inertnalTaxesTaxProperty.getAttribute(self.voucher.complement.payments.pay.relatedDocuments.relatedDocTaxRetention.relatedDocTaxRetentionStruct.BaseDR),
                                            importDR = inertnalTaxesTaxProperty.getAttribute(self.voucher.complement.payments.pay.relatedDocuments.relatedDocTaxRetention.relatedDocTaxRetentionStruct.ImporteDR),
                                            taxDR = inertnalTaxesTaxProperty.getAttribute(self.voucher.complement.payments.pay.relatedDocuments.relatedDocTaxRetention.relatedDocTaxRetentionStruct.ImpuestoDR),
                                            rateOrFeeDR = inertnalTaxesTaxProperty.getAttribute(self.voucher.complement.payments.pay.relatedDocuments.relatedDocTaxRetention.relatedDocTaxRetentionStruct.TasaOCuotaDR),
                                            factorTypeDR = inertnalTaxesTaxProperty.getAttribute(self.voucher.complement.payments.pay.relatedDocuments.relatedDocTaxRetention.relatedDocTaxRetentionStruct.TipoFactorDR)
                                        )
                            elif self.voucher.complement.payments.pay.relatedDocuments.relatedDocTaxTransport.name[5] in tax.tag:
                                inertnalTaxesTaxProperty = getSafeAttribute(tax)
                                for transportDR in inertnalTaxesTaxProperty.root:
                                    if self.voucher.complement.payments.pay.relatedDocuments.relatedDocTaxTransport.name[6] in transportDR.tag:
                                        inertnalTaxesTaxProperty = getSafeAttribute(transportDR)

                                        newRelatedDoc.TreansportTaxDR = self.voucher.complement.payments.pay.relatedDocuments.relatedDocTaxTransport(
                                            baseDR = inertnalTaxesTaxProperty.getAttribute(self.voucher.complement.payments.pay.relatedDocuments.relatedDocTaxTransport.relatedDocTaxTransportStruct.BaseDR),
                                            importDR = inertnalTaxesTaxProperty.getAttribute(self.voucher.complement.payments.pay.relatedDocuments.relatedDocTaxTransport.relatedDocTaxTransportStruct.ImporteDR),
                                            taxDR = inertnalTaxesTaxProperty.getAttribute(self.voucher.complement.payments.pay.relatedDocuments.relatedDocTaxTransport.relatedDocTaxTransportStruct.ImpuestoDR),
                                            rateOrFeeDR = inertnalTaxesTaxProperty.getAttribute(self.voucher.complement.payments.pay.relatedDocuments.relatedDocTaxTransport.relatedDocTaxTransportStruct.TasaOCuotaDR),
                                            factorTypeDR = inertnalTaxesTaxProperty.getAttribute(self.voucher.complement.payments.pay.relatedDocuments.relatedDocTaxTransport.relatedDocTaxTransportStruct.TipoFactorDR)
                                        )
                self.Voucher.Complement.Payments.Pay.RelatedDocument.append(newRelatedDoc)

            elif self.voucher.complement.payments.pay.taxPRetention.name[3] in docRelatedOrTaxP.tag:
                otherProperty = getSafeAttribute(docRelatedOrTaxP)
                for taxesp in otherProperty.root:
                    if self.voucher.complement.payments.pay.taxPRetention.name[4] in taxesp.tag:
                        taxesPInternalProperty = getSafeAttribute(taxesp)
                        for retentionP in taxesPInternalProperty.root:
                            if self.voucher.complement.payments.pay.taxPRetention.name[5] in retentionP.tag:
                                taxesPInternalProperty = getSafeAttribute(retentionP)

                                self.Voucher.Complement.Payments.Pay.TaxPRetention = self.voucher.complement.payments.pay.taxPRetention(
                                   importP =  taxesPInternalProperty.getAttribute(self.voucher.complement.payments.pay.taxPRetention.taxPRetentionStruct.ImporteP),
                                   taxP =  taxesPInternalProperty.getAttribute(self.voucher.complement.payments.pay.taxPRetention.taxPRetentionStruct.ImpuestoP)
                                )
                    elif self.voucher.complement.payments.pay.taxPTransport.name[4] in taxesp.tag:
                        taxesPInternalProperty = getSafeAttribute(taxesp)
                        for transportP in taxesPInternalProperty.root:
                            if self.voucher.complement.payments.pay.taxPTransport.name[5] in transportP.tag:
                                taxesPInternalProperty = getSafeAttribute(transportP)

                                self.Voucher.Complement.Payments.Pay.TaxPTransport = self.voucher.complement.payments.pay.taxPTransport(
                                    baseP = taxesPInternalProperty.getAttribute(self.voucher.complement.payments.pay.taxPTransport.taxPTransportStruct.BaseP),
                                    importP = taxesPInternalProperty.getAttribute(self.voucher.complement.payments.pay.taxPTransport.taxPTransportStruct.ImporteP),
                                    taxP = taxesPInternalProperty.getAttribute(self.voucher.complement.payments.pay.taxPTransport.taxPTransportStruct.ImpuestoP),
                                    rateOrFeeP = taxesPInternalProperty.getAttribute(self.voucher.complement.payments.pay.taxPTransport.taxPTransportStruct.TasaOCuotaP),
                                    factorTypeP = taxesPInternalProperty.getAttribute(self.voucher.complement.payments.pay.taxPTransport.taxPTransportStruct.TipoFactorP),
                                )
class getSafeAttribute:
    def __init__(self, root):
        self.root = root
    def getAttribute(self,attributeName):
        valueToReturn = ''
        try:
            valueToReturn = self.root.attrib[attributeName]
        finally:
            return valueToReturn
        
    def getProperty(self, propertyName):
        safeAttributeProperty = getSafeAttribute(self.root) 
        for property in self.root:
            if propertyName in property.tag :
                valueToReturn = property
                safeAttributeProperty = getSafeAttribute(root = valueToReturn)
                break
        return safeAttributeProperty
    
    def seeIfPropertyIsRepeated(self, propertyName):
        count = 0
        for componentProperty in self.root:
            if propertyName[0] in componentProperty.tag:
                safeAttributeProperty = getSafeAttribute(root = componentProperty)
                for property in safeAttributeProperty.root:
                    if propertyName[1] in property.tag:
                        count = count + 1
        return count

class fnce_xml_upld(models.Model):
    _name = 'fnce_xml_upld.fnce_xml_upld'
    _table= 'fnce_xml_upld_attachment_relation'
    _description = 'Uploads xml files and creates invoice from the info in the xml files.'
    name = fields.Text()
    date = fields.Datetime(string="Creation Date2",readonly=True)
    description = fields.Text()
    files = fields.Many2many(comodel_name="ir.attachment",
                             string="Upload XML")
    buttonVisibility = fields.Boolean()

    def setDate(self):
        for record in self:
            record.date = datetime.today()
            record.buttonVisibility = True

    @api.onchange('files')
    def changeButtonVisibility(self):
        self.buttonVisibility = False
        
    @api.model
    def searchProductByName(self, name):
        products = self.env['product.product'].search([('name', '=' ,name)],limit=100)
        if len(products) > 0:
            for product in products:
                if product.name == name:
                    return product
        else:
            return ''
        
    @api.model
    def getRetentionTaxId(self,taxAmountount):
        taxId = ''
        descrip = 'RET IVA ' + '-'+str(taxAmountount)+'%'
        taxes = self.env['tax'].search([])
        for tax in taxes:
            if descrip == tax.description:
                taxId = tax.id
                return taxId
        if taxId == '':
            taxId = self.createRetentionTax(taxAmountount)
            return taxId    

    @api.model
    def getTaxId(self,taxAmountount,taxSale):
        taxId = ''
        taxes = self.env['account.tax'].search([])
        for tax in taxes:
            if str(taxAmountount).replace('.0','') in tax.name and taxSale.lower() in tax.name.lower():
                taxId = tax.id
                return taxId
        if taxId == '':
            taxId = self.createTax(taxAmountount,taxSale)
            return taxId  
        
    @api.model
    def createRetentionTax(self,taxReference):
        name = 'RET'
        name = name + ' ' + str(taxReference)+'%'
        taxAmount = -abs(taxReference)
        descrip = 'RET ' + '-'+str(taxReference)+'%'

        retention = self.env['account.tax'].create({
            'active':'true',
            'amount':taxAmount,
            'name': name,
            'description':descrip
        })
        return retention.id

    @api.model
    def createTax(self,taxReference,taxSale):
        taxType = 'VENTAS' if taxSale == 'ventas' else 'COMPRAS'
        name = 'IVA'
        name = name + ' ' + str(taxReference)+'%' + " " + taxType
        taxAmount = taxReference 
        descrip = 'IVA ' +str(taxReference)+'%'

        tax = self.env['account.tax'].create({
            'active':'true',
            'amount':taxAmount,
            'name': name,
            'description':descrip
        })
        return tax.id

    @api.model
    def getCurrency(self,currencyText):
        currencyId = ''
        currencys = self.env['res.currency'].search([('name','like',currencyText)])
        for currency in currencys:
            if currency.name.lower() == currencyText.lower():
                currencyId = currency.id
                return currencyId
        if currencyId == '':
            return 0
   

    def getPartner(self,partnerName):
        partnerId = 0
        posiblePartners = self.env['res.partner'].search([])
        for partner in posiblePartners:
            if partner.name.lower() == partnerName.lower():
                partnerId = partner.id
                return partnerId
        if partnerId == 0:
            partnerId = self.createPartner(partnerName)
            return partnerId
        else:
            return 0
        
    def createPartner(self,partnerName):
        partner = self.env['res.partner'].create({
            'active':'true',
            'name':partnerName,
        })
        return partner.id
    
    def searchForRefWithFile(self, fileName):
        refToReturn = False
        references = self.env['fnce_xml_upld.log_reference'].search([])
        if references:
            for ref in references:
                if ref.attachmentRef.name:
                    if fileName in ref.attachmentRef.name :
                        refToReturn = ref.invoiceRef
            return refToReturn
        else:
            return refToReturn

    def seeIfFileIsUploaded(self,nameToSeach):
        isFileUploaded = False
        files = self.env['fnce_xml_upld.log_reference'].search([])
        if files != False:
            for file in files:
                if file.attachmentRef.name == nameToSeach:
                    isFileUploaded = True
                    break
        return isFileUploaded 

    def use_files(self):
        if self.files:
            for refFile in self.files:
                if self.seeIfFileIsUploaded(refFile.name):
                    self.env['bus.bus']._sendone(self.env.user.partner_id,
                    "simple_notification",
                    {
                        "title": "Custom Notification",
                        "message": "File is already uploaded.",
                        "sticky": True
                    })
                    return

                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(base64.b64decode(refFile.datas))
                    temp_file.close()
                    new_invoice = ''
                    payment = ''

                    try:
                        tree = etree.parse(temp_file.name)
                        root = tree.getroot()
                        xmlObj = xmlStruct()
                        superRoot = getSafeAttribute(root=root)
                        xmlObj.createXMLStruct(superRoot)
                        self.description = "Document Loaded"
                        if xmlObj.Voucher.voucher_type != "P":

                            currencyId = self.getCurrency(xmlObj.Voucher.currency)

                            moveType = 'out_invoice' if xmlObj.Voucher.Transmitter.name != 'HORIZON TRAILERS MEXICO' else 'in_invoice' 
                            jounal = 1 if moveType == 'out_invoice' else 2
                            taxSale = 'compras' if moveType == 'out_invoice' else 'ventas'
                            invoiceLines = []
                            for concept in xmlObj.Voucher.Concept:

                                product =self.searchProductByName(name=concept.description)
                                totalValue = float(concept.unitary_value)*float(concept.quantity)
                                discountPercantage = (float(concept.discount)*100)/totalValue if concept.discount != '' else 0
                                productId = product.id if product != '' else 0

                                taxValue = float(concept.Transport.rate_or_fee) if concept.Transport.rate_or_fee != '' else 0 
                                taxId = []
                                auxTaxId = self.getTaxId(taxValue*100,taxSale) if taxValue != 0 else 0
                                taxId.append(auxTaxId)
                                if concept.Retetnion != '':
                                    for retention in concept.Retetnion:
                                        taxRet = self.getRetentionTaxId(float(retention.rate_or_fee)*100)
                                        taxId.append(taxRet)

                                if taxId[0] == 0:
                                    taxId = []

                                invoiceLines.append((0,0,{
                                    'name': concept.description,
                                    'display_name':concept.description,
                                    'price_unit':concept.unitary_value,
                                    'quantity':concept.quantity,
                                    'discount':discountPercantage,
                                    'product_id': productId,
                                    'tax_ids': taxId,
                                    'currency_id': currencyId
                                }))
                            partnerId = self.getPartner(xmlObj.Voucher.Transmitter.name)
                            new_invoice = self.env['account.move'].create({
                                'partner_id':partnerId,
                                'date': datetime.today(),
                                'invoice_date':xmlObj.Voucher.date,
                                'move_type': moveType,
                                'journal_id':jounal,
                                'state':'draft',
                                'invoice_line_ids': invoiceLines,
                                'currency_id': currencyId,
                            })

                            {
                                'type': 'ir.actions.act_window',
                                'res_model': 'account.move',
                                'view_type': 'form',
                                'view_mode': 'tree,form',
                                'res_id': new_invoice.id,
                            }
                        else:
                        #
                            date = datetime.today()
                            payment = []
                            for document in xmlObj.Voucher.Complement.Payments.Pay.RelatedDocument:
                                documentNameRef = document.idDoc  
                                currencyId = self.getCurrency(document.currency)
                                newPayment = False
                                invoice = self.searchForRefWithFile(documentNameRef)
                                if invoice != False:
                                    if invoice.state == 'draft':
                                        invoice.action_post()
                                    newPayment = self.env['account.payment.register'].with_context(
                                            active_model='account.move',
                                            active_ids=invoice.id
                                        ).create({
                                            'payment_date': date,
                                            'amount': document.amountPayed,
                                            'currency_id': currencyId,
                                        })
                                    newPayment.action_create_payments()
                                    self.env['bus.bus']._sendone(self.env.user.partner_id,
                                        "simple_notification",
                                        {
                                            "title":"Custom Notification",
                                            "message":f"{newPayment}",
                                            "sticky":True
                                        })
                                   
                                else:
                                    self.env['bus.bus']._sendone(self.env.user.partner_id,
                                    "simple_notification",
                                    {
                                    "title": "Invoice Not Found",
                                    "message": f"Invoice ID not found {documentNameRef}.Reference 'P' was assigned.",
                                    "sticky": True
                                    })

                                    customer = self.getPartner(xmlObj.Voucher.Transmitter.name)
                                    newPayment = self.env['account.payment'].create({
                                            'date': date,
                                            'partner_id': customer,
                                            'currency_id': currencyId,
                                            'amount': document.amountPayed,
                                        })
                                payment.append(newPayment)
                    finally:
                        self.createLogReference(refFile,new_invoice,payment )
                        os.unlink(temp_file.name)
            self.description = "Finished Loading Invoices"

            self.setDate()
          
        else:

            self.description = "No files uploaded"

    def createLogReference(self,attachment,invoice,payments):
        newLogRef = self.env['fnce_xml_upld.log_reference'].create({})
        newLogRef.sudo().write({'date':datetime.today(),
                                'invoiceRef':invoice,
                                'attachmentRef':attachment,
                                })
        for payment in payments:
            if not 'register' in payment._name:
                newLogRef.paymentRef = [(4,payment.id)]
            else:
                newLogRef.paymentRelation = [(4,payment.id)]


# Message box notification
# return {
#     'type': 'ir.actions.client',
#     'tag': 'display_notification',
#     'params': {
#     'title': ('Warning'),
#     'message': f"{refFile} + {new_invoice}",
#     'sticky': True,
#     }
# }
            # self.env['bus.bus']._sendone(self.env.user.partner_id,
                #   "simple_notification",
                #   {
                    #   "title":"Custom Notification",
                    #   "message":f"{self.product_id.name}",
                    #   "sticky":True
                #   })
  
                

     