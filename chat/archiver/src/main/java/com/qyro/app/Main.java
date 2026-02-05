package com.qyro.app;
import com.qyro.adapters.Qyro;

public class Main {
    public static void main(String[] args) {
        System.out.println("Archiver started");
        // Just keeping it alive for the requirement
        while(true) {
            try { Thread.sleep(1000); } catch (InterruptedException e) {}
        }
    }
}