
FROM qyro/node-base:latest

WORKDIR /app

# Copy package.json and install service-specific dependencies
COPY package.json .
RUN npm install --production

# Copy application code
COPY . .

# Run command
CMD ["npm", "start"]
