// @ts-check
import { defineConfig } from '@hey-api/openapi-ts'

export default defineConfig({
    client: '@hey-api/client-axios',
    input: 'http://localhost:8000/api/schema/',
    output: {
        path: 'src/api/generated',
        format: 'prettier',
    },
    types: {
        enums: 'javascript',
    },
    // 不要在生成時設置 baseUrl，而是在運行時通過 api/index.ts 動態設置
})
