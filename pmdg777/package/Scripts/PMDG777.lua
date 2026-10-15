--[[
    PMDG 777 (MSFS) helper script for PilotsDeck
    Standard Script: installed into ...\com.extension.pilotsdeck.sdPlugin\Scripts by the Profile Manager.

    Used as Variable (Display) by the Profile:
        lua:PMDG777:MCP_SPD / MCP_HDG / MCP_ALT / MCP_VS
        lua:PMDG777:GEAR_STATE      (0 = up, 1 = in transit, 2 = down)
        lua:PMDG777:ZULU_CLOCK
    Used as Command by the Profile:
        lua:PMDG777:APU_START       (OFF -> START, back to ON / ON -> OFF)

    UNVERIFIED: the MCP windows are read from the simulator's standard autopilot variables below.
    Whether the PMDG 777 keeps these in sync with its MCP has not been confirmed. If a window shows
    wrong values, replace the addresses in MCP_VARS with the 777's own variables.
--]]

local MCP_VARS = {
    SPD = "(A:AUTOPILOT AIRSPEED HOLD VAR, knots)",
    MACH = "(A:AUTOPILOT MACH HOLD VAR, number)",
    HDG = "(A:AUTOPILOT HEADING LOCK DIR, degrees)",
    ALT = "(A:AUTOPILOT ALTITUDE LOCK VAR, feet)",
    VS = "(A:AUTOPILOT VERTICAL HOLD VAR, feet per minute)",
    MACH_MODE = "(A:AUTOPILOT MANAGED SPEED IN MACH, bool)",
}
for _, addr in pairs(MCP_VARS) do
    SimVar(addr)
end

SimVar("L:switch_03_a")     -- APU selector (OFF / ON / START)
SimVar("(A:GEAR CENTER POSITION, percent)")
SimVar("(A:GEAR LEFT POSITION, percent)")
SimVar("(A:GEAR RIGHT POSITION, percent)")
SimVar("(E:ZULU TIME, number)")

local function num(addr)
    local v = SimRead(addr)
    if type(v) ~= "number" then
        v = tonumber(v) or 0
    end
    return v
end

function MCP_SPD()
    if num(MCP_VARS.MACH_MODE) ~= 0 then
        return string.format(".%03d", math.floor(num(MCP_VARS.MACH) * 1000 + 0.5))
    end
    return string.format("%3d", math.floor(num(MCP_VARS.SPD) + 0.5))
end

function MCP_HDG()
    local v = math.floor(num(MCP_VARS.HDG) + 0.5) % 360
    return string.format("%03d", v)
end

function MCP_ALT()
    return string.format("%05d", math.floor(num(MCP_VARS.ALT) + 0.5))
end

function MCP_VS()
    local v = math.floor(num(MCP_VARS.VS) + 0.5)
    if v > 0 then
        return string.format("+%04d", v)
    elseif v < 0 then
        return string.format("-%04d", -v)
    end
    return "0"
end

function GEAR_STATE()
    local c = num("(A:GEAR CENTER POSITION, percent)")
    local l = num("(A:GEAR LEFT POSITION, percent)")
    local r = num("(A:GEAR RIGHT POSITION, percent)")
    if c > 99 and l > 99 and r > 99 then
        return 2
    elseif c < 1 and l < 1 and r < 1 then
        return 0
    end
    return 1
end

-- APU selector: 07 = clockwise (towards START), 08 = counter-clockwise (towards OFF)
local function apu(action, count)
    for i = 1, count, 1 do
        SimCalculator(tostring(300 + action) .. " (>K:ROTOR_BRAKE)")
        Sleep(150)
    end
end

function APU_START()
    if num("L:switch_03_a") <= 0 then
        apu(7, 2)      -- OFF -> ON -> START
        Sleep(2500)
        apu(8, 1)      -- START -> ON
    else
        apu(8, 2)      -- ON/START -> OFF (an extra click at OFF does nothing)
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
