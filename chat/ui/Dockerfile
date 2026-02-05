
FROM node:18-alpine

WORKDIR /app

COPY package.json .
RUN npm install

# Copy adapters
COPY qyro_adapters /app/qyro_adapters

COPY . .

CMD ["npm", "start"]
