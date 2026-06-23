local key = KEYS[1]
local user_id = ARGV[1]
local old_jti = ARGV[2]
local new_jti = ARGV[3]
local ttl_seconds = tonumber(ARGV[4])

local value = redis.call("GET", key)

-- 세션 만료, 로그아웃, 삭제
if not value then
    return "missing"
end

-- 문자열 -> Lua table로 변환
local ok, data = pcall(cjson.decode, value)

-- JSON 파싱 실패
if not ok then
    return "invalid"
end

-- 필요한 필드가 문자열에 존재하는지 확인
if type(data["user_id"]) ~= "string" or type(data["current_jti"]) ~= "string" then
    return "invalid"
end

-- refresh token의 user_id와 Redis 저장 user_id 비교
if data["user_id"] ~= user_id then
    return "invalid_user"
end

-- Redis와 refresh token jti 비교 -> 재사용 토큰
if data["current_jti"] ~= old_jti then
    return "reused"
end

-- 새로운 jti로 교체
data["current_jti"] = new_jti

-- 변경된 데이터 저장, TTL 갱신
redis.call("SET", key, cjson.encode(data), "EX", ttl_seconds)

return "rotated"