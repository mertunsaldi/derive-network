FROM node:20-alpine

WORKDIR /app
COPY web/viewer/package*.json ./
RUN npm install --no-fund
COPY web/viewer ./

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
