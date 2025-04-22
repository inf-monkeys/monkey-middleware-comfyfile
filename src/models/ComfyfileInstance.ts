import axios, { AxiosInstance } from "axios";
import { createLogger } from '../utils/logger.js';

// 创建 logger 实例
const logger = createLogger('comfyfile-instance');

export default class ComfyfileInstance {
  public url: string;
  public token?: string;
  public healthz?: boolean;
  public lastCheck?: Date;
  public busy: boolean;

  public axiosInstance: AxiosInstance;

  constructor({ url, token }: Pick<ComfyfileInstance, "url" | "token">) {
    this.url = url;
    this.token = token;
    this.axiosInstance = axios.create({
      baseURL: this.url,
      headers:  {
        Authorization: this.token ? `Bearer ${this.token}` : undefined,
        'Content-Type': 'application/json'
      },
    });
    this.busy = false;
  }

  async checkHealth() {
    const response = await this.axiosInstance.get("/comfyfile/healthz");

    if (response.status === 200 && response.data.success) {
      this.healthz = true;
    } else {
      this.healthz = false;
    }
    this.lastCheck = new Date();
  }
}
