import yaml from "yaml";
import fs from "fs";

interface Config {
  comfyfile_instances: {
    url: string;
    token: string;
  }[];
  health_check: {
    interval: number;
    timeout: number;
  };
  logging: {
    debug: boolean;
    retention_days: number;
    rotation_interval: number;
  };
  redis: {
    host: string;
    port: number;
    password: string;
    db: number;
    sentinel?: {
      enabled: boolean;
      master: string;
      password?: string;
      nodes: {
        host: string;
        port: number;
      }[];
    };
  };
  security?: {
    enabled?: boolean;
    secret?: string;
  };
  server?: {
    port?: number;
  };
}

const config = yaml.parse(fs.readFileSync("config.yaml", "utf8")) as Config;

export default config;