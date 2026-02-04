import React, { createContext, useContext, useEffect, useState } from 'react';
import { qyro } from './qyro-client';

const QyroContext = createContext(null);

export const QyroProvider = ({ children, gatewayUrl }) => {
    const [state, setState] = useState({});
    const [connected, setConnected] = useState(false);

    useEffect(() => {
        qyro.connect(gatewayUrl);

        qyro.onStateChange((newState) => {
            setState(newState);
        });

        const checkConnection = setInterval(() => {
            setConnected(qyro.connected);
        }, 1000);

        return () => clearInterval(checkConnection);
    }, [gatewayUrl]);

    return (
        <QyroContext.Provider value={{
            state,
            get: (k) => qyro.get(k),
            set: (k, v) => qyro.set(k, v),
            emit: (t, d) => qyro.emit(t, d),
            on: (t, h) => qyro.on(t, h),
            connected
        }}>
            {children}
        </QyroContext.Provider>
    );
};

export const useQyro = () => useContext(QyroContext);
