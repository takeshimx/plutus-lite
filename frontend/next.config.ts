import type { NextConfig } from "next";

const config: NextConfig = {
  // Cloud Run 用に、必要なファイルだけをまとめて出力する
  output: "standalone",
};

export default config;
