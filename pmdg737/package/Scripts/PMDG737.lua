--[[
    PMDG 737 (MSFS) helper script for PilotsDeck
    Standard Script: place in %appdata%\Elgato\StreamDeck\Plugins\com.extension.pilotsdeck.sdPlugin\Scripts
    (the Profile Manager does that for you when installing the .ppp package)

    Used as Variable (Display) by the Profile:
        lua:PMDG737:MCP_SPD / MCP_HDG / MCP_ALT / MCP_VS / MCP_CRS_L / MCP_CRS_R
        lua:PMDG737:GEAR_STATE      (0 = up & locked, 1 = in transit/unsafe, 2 = down & locked)
        lua:PMDG737:ZULU_CLOCK
    Used as Command by the Profile:
        lua:PMDG737:APU_START       (OFF -> START, release to ON / ON -> OFF)

    All cockpit Switches are read from the PMDG L-Vars "switch_<ID>_73X" (via MobiFlight WASM)
    and moved with "<ID><ACTION> (>K:ROTOR_BRAKE)" where ACTION 01/02 = left/right click, 07/08 = wheel up/down.
--]]

SimVar("L:ngx_SPDwindow")
SimVar("L:ngx_HDGwindow")
SimVar("L:ngx_ALTwindow")
SimVar("L:ngx_VSwindow")
SimVar("L:ngx_CRSwindowL")
SimVar("L:ngx_CRSwindowR")
SimVar("L:switch_3951_73X") -- MCP V/S light
SimVar("L:switch_118_73X")  -- APU switch (0 OFF / 50 ON / 100 START)
SimVar("L:switch_449_73X")  -- nose gear red
SimVar("L:switch_450_73X")  -- nose gear green
SimVar("L:switch_451_73X")  -- left gear red
SimVar("L:switch_452_73X")  -- right gear red
SimVar("L:switch_453_73X")  -- left gear green
SimVar("L:switch_454_73X")  -- right gear green
SimVar("(E:ZULU TIME, number)")

local function num(addr)
    local v = SimRead(addr)
    if type(v) ~= "number" then
        v = tonumber(v) or 0
    end
    return v
end

local function heading(v)
    v = math.floor(v + 0.5) % 360
    return string.format("%03d", v)
end

function MCP_SPD()
    local v = num("L:ngx_SPDwindow")
    if v <= 0 then
        return ""
    elseif v < 1 then
        return string.format(".%02d", math.floor(v * 100 + 0.5))
    else
        return string.format("%3d", math.floor(v + 0.5))
    end
end

function MCP_HDG()
    return heading(num("L:ngx_HDGwindow"))
end

function MCP_CRS_L()
    return heading(num("L:ngx_CRSwindowL"))
end

function MCP_CRS_R()
    return heading(num("L:ngx_CRSwindowR"))
end

function MCP_ALT()
    return string.format("%05d", math.floor(num("L:ngx_ALTwindow") + 0.5))
end

function MCP_VS()
    local v = math.floor(num("L:ngx_VSwindow") + 0.5)
    if v == 0 and num("L:switch_3951_73X") == 0 then
        return "-----"
    elseif v > 0 then
        return string.format("+%04d", v)
    elseif v < 0 then
        return string.format("-%04d", -v)
    else
        return "0"
    end
end

function GEAR_STATE()
    local red = num("L:switch_449_73X") + num("L:switch_451_73X") + num("L:switch_452_73X")
    local green = 0
    if num("L:switch_450_73X") > 0 then green = green + 1 end
    if num("L:switch_453_73X") > 0 then green = green + 1 end
    if num("L:switch_454_73X") > 0 then green = green + 1 end

    if red > 0 then
        return 1
    elseif green == 3 then
        return 2
    else
        return 0
    end
end

-- move the APU switch: 01 = towards START, 02 = towards OFF
local function apu_click(action, count)
    for i = 1, count, 1 do
        SimCalculator(tostring(11800 + action) .. " (>K:ROTOR_BRAKE)")
        Sleep(150)
    end
end

function APU_START()
    local pos = num("L:switch_118_73X")
    if pos < 25 then
        -- OFF -> START (hold) -> ON
        apu_click(1, 2)
        Sleep(2500)
        if num("L:switch_118_73X") > 75 then
            apu_click(2, 1)
        end
    else
        -- ON/START -> OFF
        apu_click(2, math.floor(pos / 50 + 0.5))
    end
end

function ZULU_CLOCK()
    local clock = num("(E:ZULU TIME, number)")
    if clock >= 0 then
        local hours = math.floor(clock / 3600.0)
        local minutes = math.floor((clock - (hours * 3600)) / 60)
        return string.format("%02d:%02dZ", hours, minutes)
    end
    return ""
end
