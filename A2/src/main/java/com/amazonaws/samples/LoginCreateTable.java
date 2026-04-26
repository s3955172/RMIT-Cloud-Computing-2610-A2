package com.amazonaws.samples;

import java.util.Arrays;

import com.amazonaws.client.builder.AwsClientBuilder;
import com.amazonaws.regions.Regions;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDB;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDBClientBuilder;
import com.amazonaws.services.dynamodbv2.document.DynamoDB;
import com.amazonaws.services.dynamodbv2.document.Table;
import com.amazonaws.services.dynamodbv2.document.Item;
import com.amazonaws.services.dynamodbv2.model.AttributeDefinition;
import com.amazonaws.services.dynamodbv2.model.KeySchemaElement;
import com.amazonaws.services.dynamodbv2.model.KeyType;
import com.amazonaws.services.dynamodbv2.model.ProvisionedThroughput;
import com.amazonaws.auth.profile.ProfileCredentialsProvider;
import com.amazonaws.services.dynamodbv2.model.ScalarAttributeType;

public class LoginCreateTable {

    public static void main(String[] args) throws Exception {

        AmazonDynamoDB client = AmazonDynamoDBClientBuilder.standard().withRegion(Regions.US_EAST_1).withCredentials(
                new ProfileCredentialsProvider("default")
        )  .build();

        DynamoDB dynamoDB = new DynamoDB(client);

        String tableName = "Login";
        Table table = null;

        try {
            System.out.println("Attempting to create table; please wait...");

            table = dynamoDB.createTable(
                    tableName,
                    Arrays.asList(
                            new KeySchemaElement("email", KeyType.HASH)
                    ),
                    Arrays.asList(
                            new AttributeDefinition("email", ScalarAttributeType.S)
                    ),
                    new ProvisionedThroughput(10L, 10L)
            );

            table.waitForActive();
            System.out.println("Success. Table status: " + table.getDescription().getTableStatus());

        } catch (Exception e) {
            System.err.println("Unable to create table:");
            System.err.println(e.getMessage());

            table = dynamoDB.getTable(tableName);
        }

        try {
            for (int i = 0; i <= 9; i++) {
                Item item = new Item()
                        .withPrimaryKey("email", "s4064449" + i + "@student.rmit.edu.au")
                        .withString("username", "IfazAhmer" + i)
                        .withString("password", i + "12345");

                table.putItem(item);

                System.out.println("Sample user " + i + " inserted successfully!");
            }

        } catch (Exception e) {
            System.err.println("Failed to insert item:");
            System.err.println(e.getMessage());
        }
    }
}