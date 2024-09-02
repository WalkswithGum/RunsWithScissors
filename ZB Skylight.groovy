import groovy.transform.Field

metadata {
	definition (name: "ZB", namespace: "hubitat", author: "Andy Haas", ocfDeviceType: "oic.d.switch", runLocally: true, minHubCoreVersion: '000.019.00012', executeCommandsLocally: true, genericHandler: "Zigbee") {
       
        capability "Color Temperature"
        capability "Switch"
        //for battery powered MonaLisa
        command "pwrwait", ["string"]
        command "getpwrwait"
        command "push"      

        fingerprint inClusters: "0000,0003,0004,0005,0006,1000,0008,0300,EF00", outClusters: "0000", profileId: "0104", manufacturer: "TexasInstruments", model: "TI0001", deviceJoinName: "HaasTI Thing"
	}
}

@Field String devID = "B55C"  // Skylight device ID.
@Field String devEND = "01"   // Skylight device endpoint.
@Field colorTemperature = 6000
@Field level = 1
@Field tt = 1

def parse(String description) {
    Map map = [:]
	def event = zigbee.getEvent(description)
    //log.debug "parse description: ${description}"
    if (description.startsWith("catchall")) return
    def descMap = zigbee.parseDescriptionAsMap(description)
    def value
    def name
    def text = descMap.value
    //log.debug "text: $text"
		if (descMap.clusterInt == 0) {
            //  Example: Arduino sends messages in 'L_51' format for LUX or 'K_4500' for color temp.
            if (text.startsWith("L_")){
                valL = text.substring(2,text.indexOf("."))
                valL = valL.toBigDecimal()
                level = ((valL * 5) + 1).toBigDecimal()
                state.lastL = level // Store 'level'.
                log.debug "Level: $level%" 
            }
            
             if (text.startsWith("K_")){
               valK = text.substring(2,text.indexOf("."))
               valK = valK.toBigDecimal()
               colorTemperature = ((valK * 225) + 2000).toBigDecimal()
               level = state.lastL // Retrieve 'Level'.
               log.debug "Color Temp: $colorTemperature K"
                // Once it has a K sent, go change the Skylight's lux/CT
               setColorTemperature(colorTemperature,level,tt)
            }
		}
	}

def setLevel(value,rate) { 
    rate = rate.toBigDecimal()
    def scaledRate = (rate * 10).toInteger()
    def cmd = []
    value = (value.toInteger() * 2.55).toInteger() // Makes 'value' 2 - 255.
           
    cmd = [
           "he cmd 0x${devID} 0x${devEND} 0x0008 4 {0x${intTo8bitUnsignedHex(value)} 0x${intTo16bitUnsignedHex(scaledRate)}}",
           "delay ${(rate * 1000) + 400}",
           "he rattr 0x${devID} 0x${devEND} 0x0008 0 {}"
        ]
       return cmd
    }

List<String> setColorTemperature(colorTemperature, level = null, tt = null) {
    
    log.debug "setColorTemperature(${colorTemperature}, ${level}, ${tt})"
    log.debug ""
    
    String hexValue = zigbee.swapOctets(intToHexStr((1000000/colorTemperature.toInteger()).toInteger() ,2))
    List<String> cmds = []
    BigDecimal ttSeconds = ((tt == null) ? (transitionTime == null) ? 0 : transitionTime.toInteger() / 1000 : tt).toBigDecimal()
    
        cmds.addAll(setLevel(level, ttSeconds))
        cmds.add("delay ${(ttSeconds + 1) * 1000}")
        cmds.addAll(zigbee.readAttribute(0x0008, 0x0000, [:],300))
        
        String hexTransition = zigbee.swapOctets(intToHexStr( (ttSeconds * 10).toInteger() ,2)) //this is in deca seconds
        
        cmds.add("he cmd 0x${devID} 0x${devEND} 0x0300 0x0A { ${hexValue} ${hexTransition}}")
        cmds.add("delay ${(ttSeconds + 1) * 1000}")
        cmds.addAll(zigbee.readAttribute(0x0300,0x0007,[:],0))
    
       return cmds
    }
 

def intTo16bitUnsignedHex(value) {
    def hexStr = zigbee.convertToHexString(value.toInteger(),4)
    return new String(hexStr.substring(2, 4) + hexStr.substring(0, 2))
}

def intTo8bitUnsignedHex(value) {
    return zigbee.convertToHexString(value.toInteger(), 2)
}

def on() {
    if (logEnable) log.debug "on()"
    def cmd = [
        "he cmd 0x${devID} 0x${devEND} 0x0006 1 {}",
            "delay 1000",
            "he rattr 0x${devID} 0x${devEND} 0x0006 0 {}"
    ]
    return cmd
}

def off() {
    if (logEnable) log.debug "off()"
    def cmd = [
            "he cmd 0x${devID} 0x${devEND} 0x0006 0 {}",
            "delay 1000",
            "he rattr 0x${devID} 0x${devEND} 0x0006 0 {}"
    ]
    return cmd
}
