package com.qyro.app;
import com.qyro.adapters.Qyro;

public class Main {
    public static void main(String[] args) {
        System.out.println("Logger service started");
        Qyro.publish("logs", "Java Logger Started");

        while(true) {
            try { Thread.sleep(1000); } catch (InterruptedException e) {}
        }
    }
}