# Use an official Node.js image
FROM node:20-alpine

# Set the working directory
WORKDIR /app

# Copy the package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the React code
COPY . .

# Expose the Vite development port
EXPOSE 5173

# Start the Vite server, exposing it to the Docker network
CMD ["npm", "run", "dev", "--", "--host"]